from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime

from ...core.database import get_db
from ...models.prediction import UserPrediction, PredictionScore
from ...models.f1_data import RaceWeekend
from ...schemas.prediction import PredictionCreate, PredictionResponse, PredictionScoreResponse
from ...api.deps import get_current_user
from ...schemas.user import UserResponse
from ...services.scoring_service import ScoringService

router = APIRouter(tags=["predictions"])

@router.post(
    "/",
    response_model=PredictionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new prediction",
    description="""
    Create a new prediction for a race weekend with the following information:
    - Race weekend ID
    - Top 10 prediction (comma-separated driver numbers)
    - Pole position driver
    - Sprint winner (optional)
    - Most pit stops driver
    - Fastest lap driver
    - Most positions gained driver
    
    Returns the created prediction information.
    """
)
async def create_prediction(
    prediction: PredictionCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new prediction for a race weekend.
    
    Args:
        prediction: Prediction data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        PredictionResponse: Created prediction information
        
    Raises:
        HTTPException: If race weekend not found or prediction deadline passed
    """
    # Check if race weekend exists
    result = await db.execute(select(RaceWeekend).where(RaceWeekend.id == prediction.race_weekend_id))
    race_weekend = result.scalar_one_or_none()
    
    if not race_weekend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Race weekend not found"
        )
    
    # Check if prediction deadline has passed
    if race_weekend.session_date < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prediction deadline has passed"
        )
    
    # Check if user already has a prediction for this race weekend
    stmt = select(UserPrediction).where(
        UserPrediction.user_id == current_user.id,
        UserPrediction.race_weekend_id == prediction.race_weekend_id
    )
    
    result = await db.execute(stmt)
    existing_prediction = result.scalar_one_or_none()
    
    if existing_prediction:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a prediction for this race weekend"
        )
    
    # Create prediction
    db_prediction = UserPrediction(
        user_id=current_user.id,
        race_weekend_id=prediction.race_weekend_id,
        top_10_prediction=prediction.top_10_prediction,
        pole_position=prediction.pole_position,
        sprint_winner=prediction.sprint_winner,
        most_pit_stops_driver=prediction.most_pit_stops_driver,
        fastest_lap_driver=prediction.fastest_lap_driver,
        most_positions_gained=prediction.most_positions_gained
    )
    
    db.add(db_prediction)
    await db.commit()
    await db.refresh(db_prediction)
    
    return db_prediction

@router.get(
    "/{prediction_id}",
    response_model=PredictionResponse,
    summary="Get prediction details",
    description="Returns detailed information about a specific prediction."
)
async def get_prediction(
    prediction_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific prediction by ID.
    
    Args:
        prediction_id: ID of the prediction to retrieve
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        PredictionResponse: Prediction information
        
    Raises:
        HTTPException: If prediction not found or user not authorized
    """
    # Get prediction
    result = await db.execute(select(UserPrediction).where(UserPrediction.id == prediction_id))
    prediction = result.scalar_one_or_none()
    
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )
    
    # Check if user is authorized to view this prediction
    if prediction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this prediction"
        )
    
    return prediction

@router.get(
    "/",
    response_model=List[PredictionResponse],
    summary="Get user predictions",
    description="Returns all predictions made by the current user."
)
async def get_user_predictions(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all predictions made by the current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[PredictionResponse]: List of user predictions
    """
    stmt = select(UserPrediction).where(
        UserPrediction.user_id == current_user.id
    ).order_by(UserPrediction.created_at.desc())
    
    result = await db.execute(stmt)
    predictions = result.scalars().all()
    
    return predictions 