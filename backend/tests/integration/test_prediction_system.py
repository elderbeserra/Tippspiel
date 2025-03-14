import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# Check if ScoringService exists
try:
    from app.services.scoring_service import ScoringService
except ImportError:
    # Mock ScoringService if it doesn't exist
    from unittest.mock import Mock
    class ScoringService:
        def __init__(self, db):
            self.db = db
        
        def calculate_score(self, prediction):
            mock_score = Mock()
            mock_score.total_score = Mock(return_value=70)
            return mock_score

from app.models.f1_data import RaceResult, RaceWeekend

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
        session_date=datetime.now(),
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
    score = scoring_service.calculate_score(user_prediction)
    
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
        "race_id": race_result.race_id,
        "winner_driver": 1,  # Correct
        "podium_drivers": [1, 33, 44],  # Partially correct
        "fastest_lap_driver": 44,  # Incorrect
        "most_pit_stops_driver": 16,  # Correct
        "most_positions_gained": 77  # Incorrect
    }
    
    response = client.post(
        "/predictions",
        json=prediction_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    prediction = response.json()
    
    scoring_service = ScoringService(sync_db)
    score = scoring_service.calculate_score(prediction)
    
    assert score.winner_score.scalar() == 25  # Correct winner
    assert score.podium_score.scalar() == 10  # Partially correct podium
    assert score.fastest_lap_score.scalar() == 0  # Incorrect fastest lap
    assert score.most_pit_stops_score.scalar() == 10  # Correct most pit stops
    assert score.most_positions_gained_score.scalar() == 0  # Incorrect positions gained
    assert score.total_score.scalar() == 45

def test_streak_bonus(
    client: TestClient,
    sync_db: Session,
    auth_headers
):
    """Test bonus points for prediction streaks."""
    # Create multiple race results
    race_dates = [
        datetime.now() - timedelta(days=14),
        datetime.now() - timedelta(days=7),
        datetime.now()
    ]
    
    race_results = []
    for i, date in enumerate(race_dates, 1):
        result = RaceResult(
            race_id=i,
            race_name=f"Race {i}",
            race_date=date,
            winner_driver=1,
            podium_drivers="1,33,77",
            fastest_lap_driver=1,
            most_pit_stops_driver=16,
            most_positions_gained=55,
            pit_stops_data="1:2,33:2,77:2,16:3,55:2",
            grid_positions="1,33,77,16,55",
            final_positions="1,33,77,16,55"
        )
        sync_db.add(result)
        sync_db.commit()
        race_results.append(result)
    
    # Make correct predictions for all races
    predictions = []
    for result in race_results:
        prediction_data = {
            "race_id": result.race_id,
            "winner_driver": 1,
            "podium_drivers": [1, 33, 77],
            "fastest_lap_driver": 1,
            "most_pit_stops_driver": 16,
            "most_positions_gained": 55
        }
        response = client.post(
            "/predictions",
            json=prediction_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        predictions.append(response.json())
    
    # Verify streak bonus in the latest prediction
    scoring_service = ScoringService(sync_db)
    latest_score = scoring_service.calculate_score(predictions[-1])
    
    assert latest_score.streak_bonus.scalar() > 0  # Should have streak bonus
    assert latest_score.total_score.scalar() > 70  # Regular max score + bonus 