from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from ....core.database import get_db
from ....models.f1_data import RaceWeekend as RaceWeekendModel
from ....schemas.f1_data import RaceWeekend, RaceWeekendList, Driver, DriverList
from ....services.f1_data import F1DataService
from datetime import datetime

router = APIRouter()
f1_data_service = F1DataService()

@router.get("/race-weekends/", response_model=RaceWeekendList)
async def list_race_weekends(
    db: Session = Depends(get_db),
    year: Optional[int] = Query(None, description="Filter by year"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """
    List race weekends with optional year filter.
    """
    query = db.query(RaceWeekendModel)
    
    if year:
        query = query.filter(RaceWeekendModel.year == year)
    
    total = query.count()
    items = (
        query.order_by(RaceWeekendModel.session_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return RaceWeekendList(items=[RaceWeekend.model_validate(item) for item in items], total=total)

@router.get("/race-weekends/current/", response_model=Optional[RaceWeekend])
async def get_current_race_weekend(
    db: Session = Depends(get_db)
):
    """
    Get the current or next upcoming race weekend.
    """
    now = datetime.now()
    
    # Try to find the next upcoming race
    race_weekend = (
        db.query(RaceWeekendModel)
        .filter(RaceWeekendModel.session_date >= now)
        .order_by(RaceWeekendModel.session_date)
        .first()
    )
    
    if not race_weekend:
        # If no upcoming race, return the last completed race
        race_weekend = (
            db.query(RaceWeekendModel)
            .filter(RaceWeekendModel.session_date < now)
            .order_by(RaceWeekendModel.session_date.desc())
            .first()
        )
    
    return race_weekend

@router.get("/race-weekends/{race_weekend_id}", response_model=RaceWeekend)
async def get_race_weekend(
    race_weekend_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific race weekend by ID.
    """
    race_weekend = db.query(RaceWeekendModel).filter(
        RaceWeekendModel.id == race_weekend_id
    ).first()
    
    if not race_weekend:
        raise HTTPException(status_code=404, detail="Race weekend not found")
    
    return race_weekend

@router.get("/race-weekends/year/{year}/round/{round_number}", response_model=RaceWeekend)
async def get_race_weekend_by_round(
    year: int,
    round_number: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific race weekend by year and round number.
    """
    race_weekend = db.query(RaceWeekendModel).filter(
        RaceWeekendModel.year == year,
        RaceWeekendModel.round_number == round_number
    ).first()
    
    if not race_weekend:
        raise HTTPException(status_code=404, detail="Race weekend not found")
    
    return race_weekend

@router.get("/drivers/", response_model=DriverList)
async def get_current_season_drivers(
    year: Optional[int] = Query(None, description="Year to get drivers for. Defaults to current year."),
    db: Session = Depends(get_db)
):
    """
    Get the list of drivers for the current or specified F1 season.
    
    Args:
        year: Optional year to get drivers for. If not provided, uses current year.
        db: Database session for fetching flag filenames.
        
    Returns:
        List of drivers with their numbers, names, teams, and flag filenames.
    """
    driver_dicts = await f1_data_service.get_current_season_drivers(year, db)
    drivers = [Driver(**driver) for driver in driver_dicts]
    return DriverList(items=drivers) 