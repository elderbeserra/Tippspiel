from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from contextlib import asynccontextmanager
import logging

from .sqlite_handler import SQLiteHandler
from .storage import storage_handler
from .config import settings

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    sqlite_handler = SQLiteHandler(settings.SQLITE_URL.replace("sqlite:///", ""))
    
    # Background tasks disabled due to issues with repeat_every
    logger.info("Database background tasks disabled temporarily")
    
    # @repeat_every(seconds=60*60)  # Every hour
    async def periodic_integrity_check() -> None:
        """Check database integrity hourly."""
        try:
            logger.info("Running periodic integrity check")
            sqlite_handler.check_integrity()
        except Exception as e:
            logger.error(f"Error in periodic integrity check: {e}")
    
    # @repeat_every(seconds=60*60*6)  # Every 6 hours
    async def periodic_backup() -> None:
        """Backup database every 6 hours."""
        try:
            logger.info("Running periodic backup")
            storage_handler.sync_db()
            with sqlite_handler.get_connection() as conn:
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        except Exception as e:
            logger.error(f"Error in periodic backup: {e}")
    
    # @repeat_every(seconds=60*5)  # Every 5 minutes
    async def check_wal_size() -> None:
        """Monitor WAL file size."""
        try:
            import os
            wal_file = f"{settings.SQLITE_URL.replace('sqlite:///', '')}-wal"
            if os.path.exists(wal_file):
                size_mb = os.path.getsize(wal_file) / (1024 * 1024)
                if size_mb > 50:  # WAL larger than 50MB
                    logger.warning(f"Large WAL file detected: {size_mb:.2f}MB")
                    with sqlite_handler.get_connection() as conn:
                        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        except Exception as e:
            logger.error(f"Error checking WAL size: {e}")

    # Start background tasks - disabled for now
    # periodic_integrity_check.start()
    # periodic_backup.start()
    # check_wal_size.start()
    
    # Run initial integrity check manually
    try:
        await periodic_integrity_check()
    except Exception as e:
        logger.error(f"Error in initial integrity check: {e}")
    
    yield  # Server is running
    
    # Shutdown
    try:
        logger.info("Performing final backup before shutdown")
        with sqlite_handler.get_connection() as conn:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        storage_handler.sync_db()
    except Exception as e:
        logger.error(f"Error in final backup: {e}") 