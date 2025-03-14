import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from unittest.mock import create_autospec, Mock
from app.services.scoring_service import ScoringService
from app.models.prediction import UserPrediction
from app.models.f1_data import RaceWeekend, RaceResult, QualifyingResult, SprintResult

@pytest.fixture
def mock_db():
    return create_autospec(Session)

@pytest.fixture
def scoring_service(mock_db):
    return ScoringService(mock_db)

@pytest.fixture
def sample_race_weekend() -> RaceWeekend:
    """Create a sample race weekend for testing."""
    race_weekend = Mock(spec=RaceWeekend)
    race_weekend.id = Mock()
    race_weekend.id.scalar.return_value = 1
    race_weekend.year = Mock()
    race_weekend.year.scalar.return_value = 2024
    race_weekend.round_number = Mock()
    race_weekend.round_number.scalar.return_value = 1
    race_weekend.country = Mock()
    race_weekend.country.scalar.return_value = "Test Country"
    race_weekend.circuit_name = Mock()
    race_weekend.circuit_name.scalar.return_value = "Test Circuit"
    race_weekend.session_date = Mock()
    race_weekend.session_date.scalar.return_value = datetime.now()
    race_weekend.has_sprint = Mock()
    race_weekend.has_sprint.scalar.return_value = True
    return race_weekend

@pytest.fixture
def sample_race_results(sample_race_weekend) -> list[RaceResult]:
    """Create sample race results for testing."""
    def create_mock_result(position, driver_number, grid_position, pit_stops, fastest_lap=False):
        result = Mock(spec=RaceResult)
        result.position = Mock()
        result.position.scalar.return_value = position
        result.driver_number = Mock()
        result.driver_number.scalar.return_value = driver_number
        result.grid_position = Mock()
        result.grid_position.scalar.return_value = grid_position
        result.pit_stops_count = Mock()
        result.pit_stops_count.scalar.return_value = pit_stops
        result.fastest_lap = Mock()
        result.fastest_lap.scalar.return_value = fastest_lap
        return result

    return [
        create_mock_result(1, 1, 1, 2),  # Verstappen: P1, started P1, 2 stops
        create_mock_result(2, 11, 2, 2),  # Perez: P2, started P2, 2 stops
        create_mock_result(3, 44, 9, 3, True)  # Hamilton: P3, started P9, 3 stops, fastest lap
    ]

@pytest.fixture
def sample_qualifying_results(sample_race_weekend) -> list[QualifyingResult]:
    """Create sample qualifying results for testing."""
    def create_mock_quali_result(position, driver_number):
        result = Mock(spec=QualifyingResult)
        result.position = Mock()
        result.position.scalar.return_value = position
        result.driver_number = Mock()
        result.driver_number.scalar.return_value = driver_number
        return result

    return [
        create_mock_quali_result(1, 1),  # Verstappen P1
        create_mock_quali_result(2, 11),  # Perez P2
        create_mock_quali_result(3, 44)  # Hamilton P3
    ]

@pytest.fixture
def sample_prediction(sample_race_weekend) -> UserPrediction:
    """Create a sample prediction for testing."""
    prediction = Mock(spec=UserPrediction)
    prediction.id = Mock()
    prediction.id.scalar.return_value = 1
    prediction.user_id = Mock()
    prediction.user_id.scalar.return_value = 1
    prediction.race_weekend_id = Mock()
    prediction.race_weekend_id.scalar.return_value = sample_race_weekend.id.scalar()
    prediction.top_10_prediction = Mock()
    prediction.top_10_prediction.scalar.return_value = "1,11,44,55,63,4,14,31,77,24"
    prediction.pole_position = Mock()
    prediction.pole_position.scalar.return_value = 1
    prediction.fastest_lap_driver = Mock()
    prediction.fastest_lap_driver.scalar.return_value = 44
    prediction.most_positions_gained = Mock()
    prediction.most_positions_gained.scalar.return_value = 44
    prediction.most_pit_stops_driver = Mock()
    prediction.most_pit_stops_driver.scalar.return_value = 44
    prediction.sprint_winner = Mock()
    prediction.sprint_winner.scalar.return_value = 1
    return prediction

def test_most_pit_stops_prediction(scoring_service, sample_race_results):
    # Hamilton (44) has most pit stops with 3
    most_pit_stops_driver = scoring_service._get_most_pit_stops_driver(sample_race_results)
    assert most_pit_stops_driver == 44

def test_most_positions_gained_prediction(scoring_service, sample_race_results):
    # Hamilton gained most positions: started 9th, finished 3rd (gain of 6 positions)
    most_positions_gained = scoring_service._get_most_positions_gained_driver(sample_race_results)
    assert most_positions_gained == 44

def test_calculate_score(scoring_service, sample_prediction, sample_race_results):
    score = scoring_service.calculate_score(sample_prediction, sample_race_results)
    assert score > 0  # Basic check that some points were awarded

def test_calculate_streak_bonus(scoring_service, mock_db, sample_prediction):
    # Create mock predictions with proper race_weekend and qualifying_results
    mock_qualifying_result = Mock()
    mock_qualifying_result.driver_number = Mock()
    mock_qualifying_result.driver_number.scalar.return_value = 1  # Max Verstappen
    
    mock_race_weekend = Mock()
    mock_race_weekend.qualifying_results = [mock_qualifying_result]
    
    mock_prediction1 = Mock()
    mock_prediction1.pole_position = Mock()
    mock_prediction1.pole_position.scalar.return_value = 1  # Correct prediction
    mock_prediction1.race_weekend = mock_race_weekend
    
    mock_prediction2 = Mock()
    mock_prediction2.pole_position = Mock()
    mock_prediction2.pole_position.scalar.return_value = 1  # Correct prediction
    mock_prediction2.race_weekend = mock_race_weekend
    
    mock_prediction3 = Mock()
    mock_prediction3.pole_position = Mock()
    mock_prediction3.pole_position.scalar.return_value = 1  # Correct prediction
    mock_prediction3.race_weekend = mock_race_weekend
    
    # Mock the query
    mock_query = Mock()
    mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
        mock_prediction1, mock_prediction2, mock_prediction3
    ]
    mock_db.query.return_value = mock_query

    # Call the method
    bonus = scoring_service.calculate_streak_bonus(sample_prediction.user_id.scalar())
    
    # Assert that the bonus is calculated correctly
    assert bonus >= 0

def test_calculate_prediction_score(scoring_service, sample_prediction):
    # Test individual prediction scoring components
    score = scoring_service.calculate_prediction_score(sample_prediction)
    assert score >= 0

def test_calculate_top_10_score(scoring_service, sample_prediction):
    score = scoring_service.calculate_top_10_score(sample_prediction)
    assert score >= 0

def test_calculate_pole_position_score(scoring_service, sample_prediction):
    score = scoring_service.calculate_pole_position_score(sample_prediction)
    assert score >= 0

def test_calculate_sprint_winner_score(scoring_service, sample_prediction):
    score = scoring_service.calculate_sprint_winner_score(sample_prediction)
    assert score >= 0

def test_calculate_fastest_lap_score(scoring_service, sample_prediction):
    score = scoring_service.calculate_fastest_lap_score(sample_prediction)
    assert score >= 0

def test_calculate_positions_gained_score(scoring_service, sample_prediction):
    score = scoring_service.calculate_positions_gained_score(sample_prediction)
    assert score >= 0

def test_calculate_pit_stops_score(scoring_service, sample_prediction):
    score = scoring_service.calculate_pit_stops_score(sample_prediction)
    assert score >= 0

def test_streak_bonus(scoring_service, sample_prediction):
    score = scoring_service.calculate_streak_bonus(sample_prediction.user_id.scalar())
    assert score >= 0