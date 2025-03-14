from google.cloud import storage
from google.api_core import retry
import os
from datetime import datetime
import logging
from typing import Optional

from .config import settings

logger = logging.getLogger(__name__)

class GCSStorageHandler:
    def __init__(self):
        self.client = None
        self.bucket = None
        
        # Skip GCS initialization in test environment
        if os.getenv("TESTING") != "true":
            try:
                self.client = storage.Client()
                if self.client and os.getenv("GCS_BUCKET"):
                    self.bucket = self.client.bucket(os.getenv("GCS_BUCKET"))
            except Exception as e:
                logger.error(f"Failed to initialize GCS client: {e}")

        self.db_path = settings.SQLITE_URL.replace("sqlite:///", "")
        self.backup_bucket = (
            self.client.bucket(settings.DB_BACKUP_BUCKET)
            if settings.DB_BACKUP_BUCKET
            else None
        )
    
    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def download_db(self) -> None:
        """Download SQLite database from GCS."""
        if not os.path.exists(self.db_path):
            blob = self.bucket.blob("app.db")
            blob.download_to_filename(self.db_path)
            logger.info("Downloaded database from GCS")
    
    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def upload_db(self) -> None:
        """Upload SQLite database to GCS."""
        if os.path.exists(self.db_path):
            blob = self.bucket.blob("app.db")
            blob.upload_from_filename(self.db_path)
            logger.info("Uploaded database to GCS")
    
    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def backup_db(self) -> Optional[str]:
        """Create a backup of the database in a separate bucket."""
        if not self.backup_bucket or not os.path.exists(self.db_path):
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.db"
        blob = self.backup_bucket.blob(backup_name)
        blob.upload_from_filename(self.db_path)
        logger.info(f"Created database backup: {backup_name}")
        return backup_name
    
    def init_storage(self) -> None:
        """Initialize storage and ensure bucket exists."""
        if os.getenv("TESTING") == "true":
            return
            
        if not self.client or not os.getenv("GCS_BUCKET"):
            return
            
        try:
            if not self.bucket.exists():
                self.bucket.create()
                logger.info(f"Created bucket {self.bucket.name}")
        except Exception as e:
            logger.error(f"Failed to initialize storage: {e}")
    
    def sync_db(self) -> bool:
        """Sync database with cloud storage."""
        if os.getenv("TESTING") == "true":
            return True
            
        if not self.bucket:
            return False
            
        try:
            # Upload current database
            blob = self.bucket.blob("app.db")
            blob.upload_from_filename("app.db")
            logger.info("Successfully synced database to cloud storage")
            return True
        except Exception as e:
            logger.error(f"Failed to sync database: {e}")
            return False

storage_handler = GCSStorageHandler() 