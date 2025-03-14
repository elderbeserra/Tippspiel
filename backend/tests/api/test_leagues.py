import pytest
import base64
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

def test_create_league(client: TestClient, db: Session, auth_headers):
    league_data = {
        "name": "Test League",
        "icon": None
    }
    response = client.post("/v1/leagues/", json=league_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == league_data["name"]
    assert "id" in data
    assert "created_at" in data
    assert "member_count" in data
    assert data["member_count"] == 1  # Owner is first member

def test_create_league_with_icon(client: TestClient, db: Session, auth_headers):
    # Create a small test image in base64
    test_icon = base64.b64encode(b"test_image_data").decode()
    league_data = {
        "name": "League with Icon",
        "icon": test_icon
    }
    response = client.post("/v1/leagues/", json=league_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["icon"] is not None

def test_create_league_duplicate_name(client: TestClient, db: Session, auth_headers):
    league_data = {"name": "Duplicate League"}
    # First creation
    response = client.post("/v1/leagues/", json=league_data, headers=auth_headers)
    assert response.status_code == 201
    
    # Duplicate creation
    response = client.post("/v1/leagues/", json=league_data, headers=auth_headers)
    assert response.status_code == 400
    assert "name already exists" in response.json()["detail"].lower()

def test_get_my_leagues(client: TestClient, db: Session, auth_headers):
    # Create a couple of leagues first
    league_names = ["My League 1", "My League 2"]
    for name in league_names:
        client.post("/v1/leagues/", json={"name": name}, headers=auth_headers)
    
    response = client.get("/v1/leagues/my-leagues", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert all(league["name"] in league_names for league in data[:2])

def test_get_league(client: TestClient, db: Session, auth_headers):
    # Create a league first
    league_data = {"name": "Test Get League"}
    create_response = client.post("/v1/leagues/", json=league_data, headers=auth_headers)
    league_id = create_response.json()["id"]
    
    response = client.get(f"/v1/leagues/{league_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == league_data["name"]
    assert data["id"] == league_id

def test_get_league_not_found(client: TestClient, db: Session, auth_headers):
    response = client.get("/v1/leagues/99999", headers=auth_headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_get_league_standings(client: TestClient, db: Session, auth_headers):
    # Create a league first
    league_data = {"name": "Test Standings League"}
    create_response = client.post("/v1/leagues/", json=league_data, headers=auth_headers)
    league_id = create_response.json()["id"]
    
    response = client.get(f"/v1/leagues/{league_id}/standings", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["league_id"] == league_id
    assert data["league_name"] == league_data["name"]
    assert "standings" in data
    assert isinstance(data["standings"], list)
    assert "last_updated" in data

@pytest.fixture
def test_league_id(client: TestClient, db: Session, auth_headers):
    response = client.post("/v1/leagues/", json={"name": "Test Member League"}, headers=auth_headers)
    return response.json()["id"]

def test_add_member(client: TestClient, db: Session, auth_headers, test_league_id):
    # Create another user to add
    new_user_data = {
        "email": "member@example.com",
        "username": "newmember",
        "password": "testpass123"
    }
    user_response = client.post("/auth/register", json=new_user_data)
    new_user_id = user_response.json()["id"]
    
    response = client.post(
        f"/v1/leagues/{test_league_id}/members/{new_user_id}",
        headers=auth_headers
    )
    assert response.status_code == 204

def test_remove_member(client: TestClient, db: Session, auth_headers, test_league_id):
    # Create and add a user first
    new_user_data = {
        "email": "remove@example.com",
        "username": "removeuser",
        "password": "testpass123"
    }
    user_response = client.post("/auth/register", json=new_user_data)
    new_user_id = user_response.json()["id"]
    
    # Add member
    client.post(
        f"/v1/leagues/{test_league_id}/members/{new_user_id}",
        headers=auth_headers
    )
    
    # Remove member
    response = client.delete(
        f"/v1/leagues/{test_league_id}/members/{new_user_id}",
        headers=auth_headers
    )
    assert response.status_code == 204

def test_remove_member_not_owner(
    client: TestClient,
    db: Session,
    auth_headers,
    test_league_id
):
    # Create another user
    new_user_data = {
        "email": "notowner@example.com",
        "username": "notowner",
        "password": "testpass123"
    }
    user_response = client.post("/auth/register", json=new_user_data)
    new_user_id = user_response.json()["id"]
    
    # Get token for new user
    token_response = client.post(
        "/auth/token",
        data={"username": new_user_data["email"], "password": new_user_data["password"]}
    )
    new_user_token = token_response.json()["access_token"]
    new_user_headers = {"Authorization": f"Bearer {new_user_token}"}
    
    # Try to remove a member with non-owner user
    response = client.delete(
        f"/v1/leagues/{test_league_id}/members/{new_user_id}",
        headers=new_user_headers
    )
    assert response.status_code == 400
    assert "could not remove member" in response.json()["detail"].lower() 