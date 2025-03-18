from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache
import secrets
import os

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Tippspiel"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    SQLITE_URL: str = "sqlite:///./app.db"
    GCS_BUCKET: Optional[str] = None
    DB_BACKUP_BUCKET: Optional[str] = None
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://localhost:3000",
        "https://127.0.0.1:3000",
        # Add your frontend production URL here when ready
    ]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Cloud Run
    PROJECT_ID: Optional[str] = None
    REGION: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    @property
    def is_development(self) -> bool:
        """Check if the application is running in development mode."""
        return self.DEBUG or os.environ.get("ENVIRONMENT", "").lower() == "development"
    
    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins based on environment."""
        if self.is_development:
            # In development, allow all origins for easier testing
            return ["*"]
        return self.BACKEND_CORS_ORIGINS

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

settings = get_settings() 