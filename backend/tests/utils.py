from typing import Dict, Any, Optional
from app.models.user import User
from app.models.league import League
from app.core.security import get_password_hash

def create_test_user(db, email: str = "test@example.com", username: str = "testuser", password: str = "testpass123") -> User:
    """Create a test user in the database."""
    user = User(
        email=email,
        username=username,
        hashed_password=get_password_hash(password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_test_league(db, owner_id: int, name: str = "Test League", icon: Optional[str] = None) -> League:
    """Create a test league in the database."""
    league = League(
        name=name,
        owner_id=owner_id,
        icon=icon
    )
    db.add(league)
    db.commit()
    db.refresh(league)
    return league

def assert_league_response(data: Dict[str, Any], expected_name: str, expected_owner_id: int) -> None:
    """Assert that a league response contains the expected data."""
    assert data["name"] == expected_name
    assert data["owner_id"] == expected_owner_id
    assert "id" in data
    assert "created_at" in data
    assert "member_count" in data

def assert_user_response(data: Dict[str, Any], expected_email: str, expected_username: str) -> None:
    """Assert that a user response contains the expected data."""
    assert data["email"] == expected_email
    assert data["username"] == expected_username
    assert "id" in data
    assert "created_at" in data 