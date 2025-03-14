import pytest
from pydantic import ValidationError
from app.schemas.prediction import PredictionCreate

def test_valid_prediction_create():
    valid_data = {
        "race_weekend_id": 1,
        "top_10_prediction": "1,44,11,63,55,4,16,81,23,77",
        "pole_position": 1,
        "sprint_winner": 44,
        "most_pit_stops_driver": 11,
        "fastest_lap_driver": 1,
        "most_positions_gained": 44
    }
    prediction = PredictionCreate(**valid_data)
    assert prediction.race_weekend_id == 1
    assert prediction.top_10_prediction == "1,44,11,63,55,4,16,81,23,77"

def test_invalid_race_weekend_id():
    invalid_data = {
        "race_weekend_id": 0,  # Must be > 0
        "top_10_prediction": "1,44,11,63,55,4,16,81,23,77",
        "pole_position": 1,
        "most_pit_stops_driver": 11,
        "fastest_lap_driver": 1,
        "most_positions_gained": 44
    }
    with pytest.raises(ValidationError) as exc_info:
        PredictionCreate(**invalid_data)
    assert "greater than 0" in str(exc_info.value)

def test_invalid_top_10_format():
    # Test with wrong number of drivers
    invalid_data = {
        "race_weekend_id": 1,
        "top_10_prediction": "1,44,11",  # Only 3 drivers
        "pole_position": 1,
        "most_pit_stops_driver": 11,
        "fastest_lap_driver": 1,
        "most_positions_gained": 44
    }
    with pytest.raises(ValidationError) as exc_info:
        PredictionCreate(**invalid_data)
    assert "pattern" in str(exc_info.value)

def test_duplicate_drivers():
    invalid_data = {
        "race_weekend_id": 1,
        "top_10_prediction": "1,1,11,63,55,4,16,81,23,77",  # Duplicate 1
        "pole_position": 1,
        "most_pit_stops_driver": 11,
        "fastest_lap_driver": 1,
        "most_positions_gained": 44
    }
    with pytest.raises(ValidationError) as exc_info:
        PredictionCreate(**invalid_data)
    assert "must be unique" in str(exc_info.value)

def test_negative_driver_numbers():
    invalid_data = {
        "race_weekend_id": 1,
        "top_10_prediction": "1,44,11,63,55,4,16,81,23,-1",  # Negative number
        "pole_position": 1,
        "most_pit_stops_driver": 11,
        "fastest_lap_driver": 1,
        "most_positions_gained": 44
    }
    with pytest.raises(ValidationError) as exc_info:
        PredictionCreate(**invalid_data)
    assert "String should match pattern" in str(exc_info.value)

def test_optional_sprint_winner():
    # Test with sprint winner
    valid_data = {
        "race_weekend_id": 1,
        "top_10_prediction": "1,44,11,63,55,4,16,81,23,77",
        "pole_position": 1,
        "sprint_winner": 44,
        "most_pit_stops_driver": 11,
        "fastest_lap_driver": 1,
        "most_positions_gained": 44
    }
    prediction = PredictionCreate(**valid_data)
    assert prediction.sprint_winner == 44

    # Test without sprint winner
    valid_data["sprint_winner"] = None
    prediction = PredictionCreate(**valid_data)
    assert prediction.sprint_winner is None 