import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch
from app.main import app
from app.models.f1_data import RaceWeekend
from app.schemas.f1_data import RaceWeekend as RaceWeekendSchema
from app.schemas.f1_data import RaceWeekendList
from app.api.v1.endpoints.f1_data import get_db

# Create a mock race weekend data
race_weekend_data = {
    "id": 1,
    "year": 2023,
    "round_number": 1,
    "country": "Bahrain",
    "location": "Sakhir",
    "circuit_name": "Bahrain International Circuit",
    "session_date": "2023-03-05T15:00:00",
    "has_sprint": False,
    "race_results": [],
    "qualifying_results": [],
    "sprint_results": []
}

# Mock database session
class MockDB:
    def __init__(self, return_value=None):
        self.return_value = return_value
        self.not_found_ids = [9999]  # IDs that should return 404
        
    async def __call__(self):
        yield self
        
    def query(self, *args, **kwargs):
        return self
        
    def filter(self, *args, **kwargs):
        # Check if we're filtering by ID and it's in the not_found_ids list
        for arg in args:
            if hasattr(arg, 'left') and hasattr(arg.left, 'name') and arg.left.name == 'id':
                if arg.right.value in self.not_found_ids:
                    self.return_value = None
        return self
        
    def order_by(self, *args, **kwargs):
        return self
        
    def offset(self, *args, **kwargs):
        return self
        
    def limit(self, *args, **kwargs):
        return self
        
    def all(self):
        if isinstance(self.return_value, list):
            return self.return_value
        return [self.return_value] if self.return_value else []
        
    def first(self):
        return self.return_value
        
    def count(self):
        if isinstance(self.return_value, list):
            return len(self.return_value)
        return 1 if self.return_value else 0

# Create a fixture for the test client
@pytest.fixture
def client():
    # Create a mock race weekend object
    mock_race_weekend = Mock(spec=RaceWeekend)
    for key, value in race_weekend_data.items():
        setattr(mock_race_weekend, key, value)
    
    # Create a mock DB that returns our race weekend
    mock_db = MockDB(mock_race_weekend)
    
    # Override the dependency
    app.dependency_overrides[get_db] = mock_db
    
    # Create the test client
    test_client = TestClient(app)
    
    # Yield the client for testing
    yield test_client
    
    # Clean up
    app.dependency_overrides.clear()

def test_list_race_weekends(client):
    response = client.get("/api/v1/f1/race-weekends/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)

def test_get_current_race_weekend(client):
    response = client.get("/api/v1/f1/race-weekends/current/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)

def test_get_race_weekend_by_id(client):
    response = client.get("/api/v1/f1/race-weekends/1")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)

def test_get_race_weekend_by_round(client):
    response = client.get("/api/v1/f1/race-weekends/year/2023/round/1")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)

def test_race_weekend_not_found(client):
    response = client.get("/api/v1/f1/race-weekends/9999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower() 