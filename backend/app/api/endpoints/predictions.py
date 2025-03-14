from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter(tags=["predictions"])

@router.get("/")
async def get_predictions(db: Session = Depends(get_db)):
    return {"message": "Predictions endpoint"} 