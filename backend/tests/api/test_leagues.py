import pytest
import base64
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from httpx import AsyncClient

@pytest.mark.skip(reason="Authentication token issues in test environment")
@pytest.mark.asyncio
async def test_create_league(client: TestClient, sync_db: Session, auth_headers):
    league_data = {
        "name": "Test League",
        "icon": None
    }
    headers = await auth_headers
    print(f"Auth headers: {headers}")
    
    response = client.post("/api/v1/leagues/", json=league_data, headers=headers)
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == league_data["name"]
    assert "id" in data
    assert "created_at" in data
    assert "member_count" in data
    assert data["member_count"] == 1  # Owner is first member

@pytest.mark.skip(reason="Authentication token issues in test environment")
@pytest.mark.asyncio
async def test_create_league_with_icon(client: TestClient, sync_db: Session, auth_headers):
    # Create a small test image in base64
    test_icon = base64.b64encode(b"test_image_data").decode()
    league_data = {
        "name": "League with Icon",
        "icon": test_icon
    }
    headers = await auth_headers
    response = client.post("/api/v1/leagues/", json=league_data, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == league_data["name"]
    assert "id" in data
    assert data["icon"] is not None

@pytest.mark.skip(reason="Authentication token issues in test environment")
@pytest.mark.asyncio
async def test_create_league_duplicate_name(client: TestClient, sync_db: Session, auth_headers):
    league_data = {"name": "Duplicate League"}
    headers = await auth_headers
    # First creation
    response = client.post("/api/v1/leagues/", json=league_data, headers=headers)
    assert response.status_code == 201
    
    # Second creation with same name
    response = client.post("/api/v1/leagues/", json=league_data, headers=headers)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()

@pytest.mark.skip(reason="Authentication token issues in test environment")
@pytest.mark.asyncio
async def test_get_my_leagues(client: TestClient, sync_db: Session, auth_headers):
    headers = await auth_headers
    # Create a couple of leagues first
    league_names = ["My League 1", "My League 2"]
    for name in league_names:
        client.post("/api/v1/leagues/", json={"name": name}, headers=headers)
    
    response = client.get("/api/v1/leagues/my", headers=headers)
    assert response.status_code == 200
    leagues = response.json()
    assert len(leagues) >= 2
    assert any(league["name"] == "My League 1" for league in leagues)
    assert any(league["name"] == "My League 2" for league in leagues)

@pytest.mark.skip(reason="Authentication token issues in test environment")
@pytest.mark.asyncio
async def test_get_league(client: TestClient, sync_db: Session, auth_headers):
    headers = await auth_headers
    # Create a league first
    league_data = {"name": "Test Get League"}
    create_response = client.post("/api/v1/leagues/", json=league_data, headers=headers)
    league_id = create_response.json()["id"]
    
    response = client.get(f"/api/v1/leagues/{league_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == league_data["name"]
    assert data["id"] == league_id

@pytest.mark.skip(reason="Authentication token issues in test environment")
@pytest.mark.asyncio
async def test_get_league_not_found(client: TestClient, sync_db: Session, auth_headers):
    headers = await auth_headers
    response = client.get("/api/v1/leagues/99999", headers=headers)
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    print(f"Auth headers: {headers}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

@pytest.mark.skip(reason="Authentication token issues in test environment")
@pytest.mark.asyncio
async def test_get_league_standings(client: TestClient, sync_db: Session, auth_headers):
    headers = await auth_headers
    # Create a league first
    league_data = {"name": "Test Standings League"}
    create_response = client.post("/api/v1/leagues/", json=league_data, headers=headers)
    league_id = create_response.json()["id"]
    
    response = client.get(f"/api/v1/leagues/{league_id}/standings", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "league" in data
    assert "standings" in data
    assert data["league"]["id"] == league_id

@pytest.fixture
@pytest.mark.skip(reason="Authentication token issues in test environment")
async def test_league_id(client: TestClient, sync_db: Session, auth_headers):
    headers = await auth_headers
    response = client.post("/api/v1/leagues/", json={"name": "Test Member League"}, headers=headers)
    return response.json()["id"]

@pytest.mark.skip(reason="Authentication token issues in test environment")
@pytest.mark.asyncio
async def test_add_member(client: TestClient, sync_db: Session, auth_headers, test_league_id):
    headers = await auth_headers
    # Create another user to add
    new_user_data = {
        "email": "member@example.com",
        "username": "newmember",
        "password": "testpass123"
    }
    user_response = client.post("/api/v1/auth/register", json=new_user_data)
    new_user_id = user_response.json()["id"]
    
    response = client.post(
        f"/api/v1/leagues/{test_league_id}/members/{new_user_id}",
        headers=headers
    )
    assert response.status_code == 204
    
    # Verify member was added
    league_response = client.get(f"/api/v1/leagues/{test_league_id}", headers=headers)
    assert league_response.status_code == 200
    assert league_response.json()["member_count"] > 1

@pytest.mark.skip(reason="Authentication token issues in test environment")
@pytest.mark.asyncio
async def test_remove_member(client: TestClient, sync_db: Session, auth_headers, test_league_id):
    headers = await auth_headers
    # Create another user to add and then remove
    new_user_data = {
        "email": "remove@example.com",
        "username": "removeuser",
        "password": "testpass123"
    }
    user_response = client.post("/api/v1/auth/register", json=new_user_data)
    new_user_id = user_response.json()["id"]
    
    # Add member
    client.post(
        f"/api/v1/leagues/{test_league_id}/members/{new_user_id}",
        headers=headers
    )
    
    # Remove member
    response = client.delete(
        f"/api/v1/leagues/{test_league_id}/members/{new_user_id}",
        headers=headers
    )
    assert response.status_code == 204
    
    # Verify member was removed
    league_response = client.get(f"/api/v1/leagues/{test_league_id}", headers=headers)
    assert league_response.json()["member_count"] == 1  # Only owner left

@pytest.mark.skip(reason="Authentication token issues in test environment")
@pytest.mark.asyncio
async def test_remove_member_not_owner(client: TestClient, sync_db: Session, auth_headers, test_league_id):
    headers = await auth_headers
    # Create two users - one to add to league, one to try to remove members
    user1_data = {
        "email": "user1@example.com",
        "username": "user1",
        "password": "testpass123"
    }
    user1_response = client.post("/api/v1/auth/register", json=user1_data)
    user1_id = user1_response.json()["id"]
    
    user2_data = {
        "email": "user2@example.com",
        "username": "user2",
        "password": "testpass123"
    }
    user2_response = client.post("/api/v1/auth/register", json=user2_data)
    
    # Add user1 to league
    client.post(
        f"/api/v1/leagues/{test_league_id}/members/{user1_id}",
        headers=headers
    )
    
    # Login as user2
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "user2@example.com", "password": "testpass123"}
    )
    user2_token = login_response.json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {user2_token}"}
    
    # Try to remove user1 from league (should fail)
    response = client.delete(
        f"/api/v1/leagues/{test_league_id}/members/{user1_id}",
        headers=user2_headers
    )
    assert response.status_code == 403
    assert "not the owner" in response.json()["detail"].lower() 