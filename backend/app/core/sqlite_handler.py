import sqlite3
import os
import fcntl
import time
import hashlib
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Generator
import logging
from threading import Lock
from functools import wraps

from .storage import storage_handler
from .config import settings

logger = logging.getLogger(__name__)

# Thread-safe lock for in-process synchronization
_memory_lock = Lock()

class SQLiteHandler:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.lock_file = f"{db_path}.lock"
        self._last_backup_check = datetime.now()
        self._last_integrity_check = datetime.now()
        self.backup_interval = timedelta(hours=6)  # Backup every 6 hours
        self.integrity_check_interval = timedelta(hours=1)  # Check integrity every hour
        
        # Ensure lock file exists
        if not os.path.exists(self.lock_file):
            open(self.lock_file, 'w').close()
    
    @contextmanager
    def _file_lock(self, timeout: int = 30) -> Generator[None, None, None]:
        """
        File-based locking mechanism for cross-process synchronization.
        
        Args:
            timeout: Maximum time to wait for lock in seconds
            
        Raises:
            TimeoutError: If lock cannot be acquired within timeout
        """
        start_time = time.time()
        lock_file = open(self.lock_file, 'r+')
        
        while True:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except IOError:
                if time.time() - start_time > timeout:
                    raise TimeoutError("Could not acquire database lock")
                time.sleep(0.1)
        
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()
    
    @contextmanager
    def get_connection(self, timeout: int = 30) -> Generator[sqlite3.Connection, None, None]:
        """
        Get a SQLite connection with proper locking.
        
        Args:
            timeout: Maximum time to wait for lock in seconds
            
        Yields:
            sqlite3.Connection: Database connection
        """
        with _memory_lock:  # Thread-safe lock
            with self._file_lock(timeout):  # Process-safe lock
                conn = sqlite3.connect(
                    self.db_path,
                    timeout=timeout,
                    isolation_level='IMMEDIATE'  # Important for concurrent access
                )
                conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
                conn.execute("PRAGMA busy_timeout=30000")  # 30 second busy timeout
                
                try:
                    yield conn
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    raise e
                finally:
                    conn.close()
    
    def check_integrity(self) -> bool:
        """
        Check database integrity and repair if needed.
        
        Returns:
            bool: True if database is healthy, False if corrupted
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()[0]
                
                if result != "ok":
                    logger.error(f"Database corruption detected: {result}")
                    self._handle_corruption()
                    return False
                
                # Check for WAL file size
                if os.path.exists(f"{self.db_path}-wal"):
                    wal_size = os.path.getsize(f"{self.db_path}-wal")
                    if wal_size > 50 * 1024 * 1024:  # 50MB
                        logger.warning("Large WAL file detected, checkpointing...")
                        cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                
                return True
        except Exception as e:
            logger.error(f"Error checking database integrity: {e}")
            return False
    
    def _handle_corruption(self) -> None:
        """Handle database corruption by restoring from backup."""
        logger.critical("Attempting to recover from database corruption")
        
        # Create corruption report
        corrupt_file = f"{self.db_path}.corrupt.{int(time.time())}"
        os.rename(self.db_path, corrupt_file)
        
        # Download fresh copy from GCS
        storage_handler.download_db()
        
        # Verify new copy
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            if cursor.fetchone()[0] != "ok":
                raise Exception("Backup copy is also corrupted")
    
    def periodic_maintenance(self) -> None:
        """Perform periodic maintenance tasks."""
        now = datetime.now()
        
        # Check integrity
        if now - self._last_integrity_check >= self.integrity_check_interval:
            self.check_integrity()
            self._last_integrity_check = now
        
        # Backup if needed
        if now - self._last_backup_check >= self.backup_interval:
            storage_handler.sync_db()
            self._last_backup_check = now
    
    def calculate_checksum(self) -> str:
        """Calculate SHA-256 checksum of the database file."""
        with open(self.db_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

def with_db_maintenance(f):
    """Decorator to perform periodic maintenance around database operations."""
    @wraps(f)
    async def wrapper(*args, **kwargs):
        handler = SQLiteHandler(settings.SQLITE_URL.replace("sqlite:///", ""))
        try:
            handler.periodic_maintenance()
            # Handle async generator
            async_gen = f(*args, **kwargs)
            try:
                # Yield the first value from the generator
                yield await async_gen.__anext__()
                # Continue yielding any remaining values
                while True:
                    try:
                        yield await async_gen.__anext__()
                    except StopAsyncIteration:
                        break
            except sqlite3.DatabaseError as e:
                if "database disk image is malformed" in str(e):
                    handler.check_integrity()
                    # Try again after fixing integrity issues
                    async_gen = f(*args, **kwargs)
                    async for value in async_gen:
                        yield value
                else:
                    raise
            finally:
                # Ensure the generator is properly closed
                try:
                    await async_gen.aclose()
                except (AttributeError, StopAsyncIteration):
                    pass
        except sqlite3.DatabaseError as e:
            if "database disk image is malformed" in str(e):
                handler.check_integrity()
                # Try again after fixing integrity issues
                async_gen = f(*args, **kwargs)
                async for value in async_gen:
                    yield value
            else:
                raise
    return wrapper 