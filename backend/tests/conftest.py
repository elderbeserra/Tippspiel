import os
import sys
from typing import AsyncGenerator, Generator
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.database import Base, get_db
from app.main import app
from app.models.user import User  # Import all models to ensure they're registered with Base.metadata
from app.models.league import League
from app.models.prediction import UserPrediction, PredictionScore
from app.models.f1_data import RaceWeekend, RaceResult, QualifyingResult, SprintResult
from app.core.security import get_password_hash
from sqlalchemy import select
import asyncio

# Set up test database - use a file-based database for testing
TEST_DATABASE_URL = "sqlite:///./test.db"

# Create a synchronous engine for creating tables
sync_engine = create_engine(TEST_DATABASE_URL)

# Create an async engine for the application
engine = create_async_engine(
    TEST_DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///"), 
    echo=True
)

TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Initialize database
@pytest.fixture(scope="session", autouse=True)
def initialize_db():
    """Initialize the database once for the entire test session."""
    # Remove test database if it exists
    if os.path.exists("./test.db"):
        os.remove("./test.db")
        
    # Create tables using synchronous engine
    Base.metadata.create_all(bind=sync_engine)
    yield
    # Clean up after tests
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async_session = TestingSessionLocal()
    try:
        yield async_session
    finally:
        await async_session.rollback()
        await async_session.close()

@pytest.fixture
def sync_db() -> Generator[Session, None, None]:
    """Create a fresh synchronous database session for each test."""
    # Create a synchronous session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
def test_app() -> FastAPI:
    """Create a fresh app for each test."""
    # Override settings for testing
    from app.core.config import settings
    settings.SECRET_KEY = "test_secret_key_for_testing_only"
    return app

@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    """Create a test client."""
    # Create a client without using the context manager
    client = TestClient(test_app)
    return client

@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    async with AsyncClient(base_url="http://test") as client:
        yield client

@pytest.fixture
async def async_test_user(db: AsyncGenerator[AsyncSession, None]) -> User:
    """Create a test user directly in the database using async session."""
    # Get the session from the generator
    session = None
    async for s in db:
        session = s
        break
    
    if not session:
        raise RuntimeError("Could not get database session")
    
    # Check if user already exists
    query = select(User).where(User.email == "test@example.com")
    result = await session.execute(query)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        return existing_user
        
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpass123")
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@pytest.fixture
def sync_test_user(sync_db: Session) -> User:
    """Create a test user directly in the database using synchronous session."""
    # Check if user already exists
    existing_user = sync_db.query(User).filter(User.email == "test@example.com").first()
    
    if existing_user:
        return existing_user
        
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpass123")
    )
    sync_db.add(user)
    sync_db.commit()
    sync_db.refresh(user)
    return user

@pytest.fixture
async def auth_headers(async_test_user: User) -> dict:
    """Create authentication headers for a test user."""
    from app.core.security import create_access_token
    from app.core.config import settings
    
    # Ensure we're using the test secret key
    settings.SECRET_KEY = "test_secret_key_for_testing_only"
    
    # Get the user
    user = await async_test_user
    
    # Create token directly
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {access_token}"}

# Override the get_db dependency
async def override_get_db():
    """Override the get_db dependency for testing."""
    # Create a new session
    async_session = TestingSessionLocal()
    try:
        yield async_session
    finally:
        await async_session.rollback()
        await async_session.close()

# Override the dependency
app.dependency_overrides[get_db] = override_get_db

# Set testing environment
os.environ["TESTING"] = "1" 