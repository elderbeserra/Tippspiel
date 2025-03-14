from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict
import time

from ...core.database import get_db

router = APIRouter(tags=["health"])

@router.get("/health/live", response_model=Dict[str, str])
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    Simple check to verify the application is running.
    """
    return {"status": "alive"}

@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Kubernetes readiness probe endpoint.
    Verifies that the application can handle requests by checking:
    - Database connection
    - Any other external service dependencies
    """
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        
        return {
            "status": "ready",
            "checks": {
                "database": "healthy"
            },
            "timestamp": time.time()
        }
    except Exception as e:
        return Response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=str(e)
        ) 