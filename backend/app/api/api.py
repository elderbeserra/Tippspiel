from fastapi import APIRouter
from .endpoints import auth, leagues, predictions, admin
from .v1.endpoints import f1_data

api_router = APIRouter()

# Include routers for different endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(leagues.router, prefix="/leagues", tags=["leagues"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
api_router.include_router(f1_data.router, prefix="/f1", tags=["f1_data"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"]) 