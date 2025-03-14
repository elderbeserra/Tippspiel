from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache
import secrets

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
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
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

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

settings = get_settings() 