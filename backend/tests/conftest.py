import os
import sys
from typing import AsyncGenerator, Generator
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.database import Base, get_db
from app.main import app
from app.models.user import User  # Import all models to ensure they're registered with Base.metadata
from app.models.league import League
from app.models.prediction import UserPrediction, PredictionScore
from app.models.f1_data import RaceWeekend, RaceResult, QualifyingResult, SprintResult

# Set up test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database for each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = TestingSessionLocal()
    try:
        yield async_session
    finally:
        await async_session.rollback()
        await async_session.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def test_app() -> FastAPI:
    """Create a fresh app for each test."""
    return app

@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    # Create a client without using the context manager
    client = TestClient(app)
    return client

@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    async with AsyncClient(base_url="http://test") as client:
        yield client

@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    """Create authentication headers for a test user."""
    # Create a test user
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    # Login and get token
    response = client.post("/api/v1/auth/token", data={
        "username": user_data["email"],
        "password": user_data["password"]
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# Override the get_db dependency
async def override_get_db():
    """Override the get_db dependency for testing."""
    async with TestingSessionLocal() as session:
        yield session

# Override the dependency
app.dependency_overrides[get_db] = override_get_db

# Set testing environment
os.environ["TESTING"] = "1" 