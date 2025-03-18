import time
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.f1_data import RaceWeekend, RaceResult


def measure_response_time(client: TestClient, method: str, url: str, **kwargs) -> float:
    """Measure response time for an endpoint."""
    start_time = time.time()
    response = client.request(method, url, **kwargs)
    assert response.status_code in (200, 201, 204)  # Ensure request was successful
    return time.time() - start_time

def test_auth_endpoint_performance(client: TestClient, sync_db: Session):
    """Test authentication endpoints performance."""
    # Test registration performance
    registration_times = []
    for i in range(10):
        user_data = {
            "email": f"perf_test{i}@example.com",
            "username": f"perftest{i}",
            "password": "testpass123"
        }
        time_taken = measure_response_time(
            client, "POST", "/api/v1/auth/register",
            json=user_data
        )
        registration_times.append(time_taken)
    
    avg_registration_time = sum(registration_times) / len(registration_times)
    assert avg_registration_time < 1.0  # Registration should take less than 1 second
    
    # Test login performance
    login_times = []
    for i in range(10):
        time_taken = measure_response_time(
            client, "POST", "/api/v1/auth/token",
            data={
                "username": f"perf_test{i}@example.com",
                "password": "testpass123"
            }
        )
        login_times.append(time_taken)
    
    avg_login_time = sum(login_times) / len(login_times)
    assert avg_login_time < 0.5  # Login should take less than 0.5 seconds

def test_league_endpoints_performance(
    client: TestClient,
    sync_db: Session,
    auth_headers
):
    """Test league endpoints performance under load."""
    # Create multiple leagues
    league_creation_times = []
    league_ids = []
    
    for i in range(5):
        league_data = {"name": f"Performance League {i}"}
        time_taken = measure_response_time(
            client, "POST", "/api/v1/leagues/",
            json=league_data,
            headers=auth_headers
        )
        league_creation_times.append(time_taken)
        response = client.post("/api/v1/leagues/", json=league_data, headers=auth_headers)
        league_ids.append(response.json()["id"])
    
    avg_creation_time = sum(league_creation_times) / len(league_creation_times)
    assert avg_creation_time < 0.5  # League creation should take less than 0.5 seconds
    
    # Test concurrent league standings requests
    def get_league_standings(league_id: int) -> float:
        return measure_response_time(
            client,
            "GET",
            f"/api/v1/leagues/{league_id}/standings",
            headers=auth_headers
        )
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(get_league_standings, league_id)
            for league_id in league_ids
        ]
        standings_times = [future.result() for future in as_completed(futures)]
    
    avg_standings_time = sum(standings_times) / len(standings_times)
    assert avg_standings_time < 0.5  # Standings retrieval should take less than 500ms

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
    sync_db.add(result)
    sync_db.commit()
    sync_db.refresh(result)
    return result

def test_prediction_submission_performance(
    client: TestClient,
    sync_db: Session,
    auth_headers,
    race_result
):
    """Test prediction submission performance under load."""
    prediction_times = []
    
    # Submit multiple predictions concurrently
    def submit_prediction() -> float:
        prediction_data = {
            "race_weekend_id": race_result.race_weekend_id,
            "top_10_prediction": "1,33,44,16,55,4,14,31,22,10",
            "pole_position": 1,
            "fastest_lap_driver": 33,
            "most_pit_stops_driver": 16,
            "most_positions_gained": 55,
            "sprint_winner": None
        }
        return measure_response_time(
            client,
            "POST",
            "/api/v1/predictions/",
            json=prediction_data,
            headers=auth_headers
        )
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(submit_prediction) for _ in range(20)]
        prediction_times = [future.result() for future in as_completed(futures)]
    
    avg_prediction_time = sum(prediction_times) / len(prediction_times)
    assert avg_prediction_time < 0.4  # Prediction submission should take less than 400ms
    
    # Verify 95th percentile
    sorted_times = sorted(prediction_times)
    percentile_95 = sorted_times[int(len(sorted_times) * 0.95)]
    assert percentile_95 < 0.6  # 95% of submissions should be under 600ms

def test_race_results_performance(client: TestClient, sync_db: Session, auth_headers):
    """Test race results endpoint performance."""
    # Get multiple race results concurrently
    def get_race_result(race_id: int) -> float:
        return measure_response_time(
            client,
            "GET",
            f"/api/v1/f1/race-weekends/{race_id}",
            headers=auth_headers
        )
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(get_race_result, i) for i in range(1, 6)]
        result_times = [future.result() for future in as_completed(futures)]
    
    avg_result_time = sum(result_times) / len(result_times)
    assert avg_result_time < 0.3  # Race results retrieval should take less than 300ms 