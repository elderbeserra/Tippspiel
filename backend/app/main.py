from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from .core.config import settings
from .core.logging import setup_logging
from .core.middleware import setup_middleware
from .api.api import api_router
from .tasks.f1_sync import schedule_sync
from fastapi_utils.tasks import repeat_every
from .core.tasks import lifespan as db_lifespan
from .core.exceptions import (
    BaseAPIException, 
    api_exception_handler, 
    validation_exception_handler, 
    http_exception_handler,
    general_exception_handler
)
from contextlib import asynccontextmanager
import logging

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Store the background task
f1_sync_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start F1 sync scheduler (disabled for now to fix startup issues)
    logger.info("Starting F1 sync scheduler (disabled)")
    # Uncomment this when F1 sync is needed
    # try:
    #     await schedule_sync()
    # except Exception as e:
    #     logger.error(f"Error starting F1 sync: {e}")
    
    logger.info("Starting database lifespan")
    async with db_lifespan(app):
        logger.info(f"{settings.APP_NAME} startup complete")
        yield
    
    logger.info(f"{settings.APP_NAME} shutdown complete")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="""
    Formula 1 Prediction Game API.
    
    This API provides endpoints for:
    - User authentication and management
    - League creation and management
    - F1 race predictions and scoring
    - Admin operations for system management
    
    For more details on each endpoint, see the specific route documentation.
    """,
    contact={
        "name": "Development Team",
        "email": "dev@tippspiel.example.com",
    },
    license_info={
        "name": "Private",
        "url": "https://example.com/license",
    },
    openapi_tags=[
        {
            "name": "auth",
            "description": "Authentication operations including registration, login, and token management",
        },
        {
            "name": "leagues",
            "description": "League management including creation, member management, and standings",
        },
        {
            "name": "predictions",
            "description": "F1 race predictions and scoring",
        },
        {
            "name": "f1_data",
            "description": "Formula 1 race data including schedules, results, and statistics",
        },
        {
            "name": "admin",
            "description": "Admin-only operations for system management",
        },
        {
            "name": "health",
            "description": "Health check endpoints for monitoring system status",
        },
    ],
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Register exception handlers
app.add_exception_handler(BaseAPIException, api_exception_handler)  # type: ignore
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore
app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore
app.add_exception_handler(Exception, general_exception_handler)  # type: ignore

# Set up middleware
setup_middleware(app)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Log application startup
logger.info(
    f"Application {settings.APP_NAME} v{settings.VERSION} initialized",
    extra={
        "environment": "development" if settings.is_development else "production",
        "debug_mode": settings.DEBUG,
        "api_prefix": settings.API_V1_STR,
    }
) 