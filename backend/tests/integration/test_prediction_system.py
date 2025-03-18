import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from unittest.mock import Mock

# Import the ScoringService directly
from app.services.scoring_service import ScoringService
from app.models.f1_data import RaceResult, RaceWeekend, QualifyingResult

@pytest.fixture
def race_result(sync_db: Session):
    """Create a test race result."""
    # First create a race weekend
    race_weekend = RaceWeekend(
        year=2023,
        round_number=1,
        country="Test Country",
        location="Test Location",
        circuit_name="Test Circuit",
        session_date=datetime.now() + timedelta(days=1),
        has_sprint=False
    )
    sync_db.add(race_weekend)
    sync_db.commit()
    sync_db.refresh(race_weekend)
    
    # Now create race results
    result = RaceResult(
        race_weekend_id=race_weekend.id,
        position=1,
        driver_number=1,  # Hamilton
        driver_name="Lewis Hamilton",
        team="Mercedes",
        grid_position=1,
        status="Finished",
        points=25.0,
        fastest_lap=True,
        fastest_lap_time="1:30.000",
        first_pit_lap=20,
        first_pit_time="25:30.000",
        pit_stops_count=2
    )
    sync_db.add(result)
    sync_db.commit()
    sync_db.refresh(result)
    return result

@pytest.fixture
def user_prediction(sync_db: Session, race_result, auth_headers, client):
    """Create a test user prediction."""
    prediction_data = {
        "race_weekend_id": race_result.race_weekend_id,
        "top_10_prediction": "1,33,77,16,55,4,14,31,22,10",
        "pole_position": 1,
        "fastest_lap_driver": 33,
        "most_pit_stops_driver": 16,
        "most_positions_gained": 55,
        "sprint_winner": None
    }
    response = client.post(
        "/api/v1/predictions/",
        json=prediction_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    return response.json()

def test_full_prediction_flow(
    client: TestClient,
    sync_db: Session,
    race_result,
    user_prediction,
    auth_headers
):
    """Test the full prediction flow from submission to scoring."""
    # Verify prediction was saved
    response = client.get(
        f"/api/v1/predictions/{user_prediction['id']}",
        headers=auth_headers
    )
    assert response.status_code == 200
    saved_prediction = response.json()
    assert saved_prediction["race_weekend_id"] == race_result.race_weekend_id
    
    # Calculate scores
    scoring_service = ScoringService(sync_db)
    race_results = sync_db.query(RaceResult).filter(RaceResult.race_weekend_id == race_result.race_weekend_id).all()
    score = scoring_service.calculate_score(user_prediction, race_results)
    
    # Verify all scoring components
    assert score.total_score > 0  # Some points should be awarded

def test_partial_prediction_scoring(
    client: TestClient,
    sync_db: Session,
    auth_headers,
    race_result
):
    """Test scoring with partially correct predictions."""
    prediction_data = {
        "race_weekend_id": race_result.race_weekend_id,
        "top_10_prediction": "1,33,44,16,55,4,14,31,22,10",  # Partially correct
        "pole_position": 1,  # Correct
        "fastest_lap_driver": 44,  # Incorrect
        "most_pit_stops_driver": 16,  # Correct
        "most_positions_gained": 77,  # Incorrect
        "sprint_winner": None
    }
    
    response = client.post(
        "/api/v1/predictions/",
        json=prediction_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    prediction = response.json()
    
    scoring_service = ScoringService(sync_db)
    race_results = sync_db.query(RaceResult).filter(RaceResult.race_weekend_id == race_result.race_weekend_id).all()
    score = scoring_service.calculate_score(prediction, race_results)
    
    # Check individual score components
    assert score.pole_position_score == 5  # Correct pole position
    assert score.fastest_lap_score == 0  # Incorrect fastest lap
    assert score.most_pit_stops_score == 10  # Correct most pit stops
    assert score.most_positions_gained_score == 0  # Incorrect positions gained
    assert score.total_score > 0  # Some points should be awarded

def test_streak_bonus(
    client: TestClient,
    sync_db: Session,
    auth_headers
):
    """Test bonus points for prediction streaks."""
    # Create multiple race weekends
    race_dates = [
        datetime.now() + timedelta(days=1),
        datetime.now() + timedelta(days=8),
        datetime.now() + timedelta(days=15)
    ]
    
    race_weekends = []
    for i, date in enumerate(race_dates, 1):
        race_weekend = RaceWeekend(
            year=2023,
            round_number=i,
            country=f"Test Country {i}",
            location=f"Test Location {i}",
            circuit_name=f"Test Circuit {i}",
            session_date=date,
            has_sprint=False
        )
        sync_db.add(race_weekend)
        sync_db.commit()
        sync_db.refresh(race_weekend)
        
        # Add qualifying results
        quali_result = QualifyingResult(
            race_weekend_id=race_weekend.id,
            position=1,
            driver_number=1,
            driver_name="Lewis Hamilton",
            team="Mercedes",
            q1_time="1:20.000",
            q2_time="1:19.500",
            q3_time="1:19.000"
        )
        sync_db.add(quali_result)
        
        # Add race results
        race_result = RaceResult(
            race_weekend_id=race_weekend.id,
            position=1,
            driver_number=1,
            driver_name="Lewis Hamilton",
            team="Mercedes",
            grid_position=1,
            status="Finished",
            points=25.0,
            fastest_lap=True,
            fastest_lap_time="1:30.000",
            first_pit_lap=20,
            first_pit_time="25:30.000",
            pit_stops_count=2
        )
        sync_db.add(race_result)
        sync_db.commit()
        race_weekends.append(race_weekend)
    
    # Make correct predictions for all races
    predictions = []
    for race_weekend in race_weekends:
        prediction_data = {
            "race_weekend_id": race_weekend.id,
            "top_10_prediction": "1,33,44,16,55,4,14,31,22,10",
            "pole_position": 1,
            "fastest_lap_driver": 1,
            "most_pit_stops_driver": 16,
            "most_positions_gained": 55,
            "sprint_winner": None
        }
        response = client.post(
            "/api/v1/predictions/",
            json=prediction_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        predictions.append(response.json())
    
    # Verify streak bonus in the latest prediction
    scoring_service = ScoringService(sync_db)
    race_results = sync_db.query(RaceResult).filter(RaceResult.race_weekend_id == race_weekends[-1].id).all()
    latest_score = scoring_service.calculate_score(predictions[-1], race_results)
    
    assert latest_score.streak_bonus > 0  # Should have streak bonus
    assert latest_score.total_score > 70  # Regular max score + bonus 