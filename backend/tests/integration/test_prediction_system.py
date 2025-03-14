import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.services.scoring_service import ScoringService
from app.models.f1_data import RaceResult

@pytest.fixture
def race_result(db: Session):
    """Create a test race result."""
    result = RaceResult(
        race_id=1,
        race_name="Test Grand Prix",
        race_date=datetime.now(),
        winner_driver=1,  # Hamilton
        podium_drivers="1,33,77",  # Hamilton, Verstappen, Bottas
        fastest_lap_driver=33,  # Verstappen
        most_pit_stops_driver=16,  # Leclerc
        most_positions_gained=55,  # Sainz
        pit_stops_data="1:2,33:3,77:2,16:4,55:2",  # Driver:Stops
        grid_positions="33,1,77,16,55",  # Starting grid
        final_positions="1,33,77,16,55"  # Final positions
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result

@pytest.fixture
def user_prediction(db: Session, race_result, auth_headers, client):
    """Create a test user prediction."""
    prediction_data = {
        "race_id": race_result.race_id,
        "winner_driver": 1,
        "podium_drivers": [1, 33, 77],
        "fastest_lap_driver": 33,
        "most_pit_stops_driver": 16,
        "most_positions_gained": 55
    }
    response = client.post(
        "/predictions",
        json=prediction_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    return response.json()

def test_full_prediction_flow(
    client: TestClient,
    db: Session,
    auth_headers,
    race_result,
    user_prediction
):
    """Test the complete prediction flow from submission to scoring."""
    # Verify prediction was saved correctly
    response = client.get(
        f"/predictions/{user_prediction['id']}",
        headers=auth_headers
    )
    assert response.status_code == 200
    saved_prediction = response.json()
    assert saved_prediction["race_id"] == race_result.race_id
    assert saved_prediction["winner_driver"] == 1
    
    # Calculate scores
    scoring_service = ScoringService(db)
    score = scoring_service.calculate_score(user_prediction)
    
    # Verify all scoring components
    assert score.winner_score.scalar() == 25  # Correct winner prediction
    assert score.podium_score.scalar() == 15  # Correct podium prediction
    assert score.fastest_lap_score.scalar() == 10  # Correct fastest lap
    assert score.most_pit_stops_score.scalar() == 10  # Correct most pit stops
    assert score.most_positions_gained_score.scalar() == 10  # Correct positions gained
    assert score.total_score.scalar() == 70  # Sum of all points

def test_partial_prediction_scoring(
    client: TestClient,
    db: Session,
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
    
    scoring_service = ScoringService(db)
    score = scoring_service.calculate_score(prediction)
    
    assert score.winner_score.scalar() == 25  # Correct winner
    assert score.podium_score.scalar() == 10  # Partially correct podium
    assert score.fastest_lap_score.scalar() == 0  # Incorrect fastest lap
    assert score.most_pit_stops_score.scalar() == 10  # Correct most pit stops
    assert score.most_positions_gained_score.scalar() == 0  # Incorrect positions gained
    assert score.total_score.scalar() == 45

def test_streak_bonus(
    client: TestClient,
    db: Session,
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
        db.add(result)
        db.commit()
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
    scoring_service = ScoringService(db)
    latest_score = scoring_service.calculate_score(predictions[-1])
    
    assert latest_score.streak_bonus.scalar() > 0  # Should have streak bonus
    assert latest_score.total_score.scalar() > 70  # Regular max score + bonus 