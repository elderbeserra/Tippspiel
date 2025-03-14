from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from contextlib import contextmanager
from typing import Generator, AsyncGenerator
import logging

from .config import settings
from .sqlite_handler import SQLiteHandler, with_db_maintenance

logger = logging.getLogger(__name__)

# Initialize SQLite handler
sqlite_handler = SQLiteHandler(settings.SQLITE_URL.replace("sqlite:///", ""))

# Create SQLAlchemy engine with custom connect/disconnect handlers
def _engine_connect(dbapi_connection, connection_record):
    """Set SQLite pragmas on connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.close()

engine = create_engine(
    settings.SQLITE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,  # Enable connection health checks
    pool_size=5,  # Limit concurrent connections
    max_overflow=10  # Allow up to 10 additional connections
)

# Register connection event
event.listen(engine, 'connect', _engine_connect)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Get database session with proper locking and maintenance.
    To be used in background tasks and scripts.
    """
    with sqlite_handler.get_connection():  # Ensure file-level locking
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

@with_db_maintenance
async def get_db() -> AsyncGenerator[Session, None]:
    """
    Get database session for FastAPI dependency injection.
    Includes automatic maintenance checks.
    """
    with sqlite_handler.get_connection():  # Ensure file-level locking
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

def init_db() -> None:
    """Initialize database and create tables."""
    try:
        # Ensure we have the latest version from GCS
        from .storage import storage_handler
        storage_handler.init_storage()
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Verify database integrity
        sqlite_handler.check_integrity()
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise 