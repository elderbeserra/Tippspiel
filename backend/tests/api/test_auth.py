from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

def test_register_user(client: TestClient, db: Session):
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123"
    }
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert "id" in data
    assert "password" not in data

def test_register_duplicate_email(client: TestClient, db: Session):
    user_data = {
        "email": "duplicate@example.com",
        "username": "uniqueuser",
        "password": "testpass123"
    }
    # First registration
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    
    # Try registering with same email
    user_data["username"] = "differentuser"
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 400
    assert "email already registered" in response.json()["detail"].lower()

def test_register_duplicate_username(client: TestClient, db: Session):
    user_data = {
        "email": "user1@example.com",
        "username": "sameusername",
        "password": "testpass123"
    }
    # First registration
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    
    # Try registering with same username
    user_data["email"] = "user2@example.com"
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 400
    assert "username already taken" in response.json()["detail"].lower()

def test_login_success(client: TestClient, db: Session):
    # Create user first
    user_data = {
        "email": "login@example.com",
        "username": "loginuser",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    # Try logging in
    response = client.post(
        "/api/v1/auth/token",
        data={"username": user_data["email"], "password": user_data["password"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client: TestClient, db: Session):
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "wrong@example.com", "password": "wrongpass"}
    )
    assert response.status_code == 401
    assert "incorrect email or password" in response.json()["detail"].lower()

def test_get_current_user(client: TestClient, auth_headers: dict):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert "username" in data
    assert "password" not in data

def test_get_current_user_invalid_token(client: TestClient):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert "could not validate credentials" in response.json()["detail"].lower() 