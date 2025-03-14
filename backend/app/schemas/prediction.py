from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class PredictionCreate(BaseModel):
    race_weekend_id: int = Field(..., gt=0)
    top_10_prediction: str = Field(
        ...,
        description="Comma-separated list of driver numbers for top 10 prediction",
        pattern=r"^\d+(,\d+){9}$"  # Exactly 10 numbers separated by commas
    )
    pole_position: int = Field(..., gt=0)
    sprint_winner: Optional[int] = Field(None, gt=0)
    most_pit_stops_driver: int = Field(..., gt=0)
    fastest_lap_driver: int = Field(..., gt=0)
    most_positions_gained: int = Field(..., gt=0)
    
    @field_validator('top_10_prediction')
    @classmethod
    def validate_top_10_format(cls, v):
        try:
            numbers = [int(x) for x in v.split(',')]
        except ValueError:
            raise ValueError('All values must be valid integers')
            
        if len(numbers) != 10:
            raise ValueError('Must provide exactly 10 driver numbers')
            
        if len(set(numbers)) != len(numbers):
            raise ValueError('Driver numbers must be unique')
            
        if any(n <= 0 for n in numbers):
            raise ValueError('All driver numbers must be positive')
            
        return v
    
    @field_validator('sprint_winner')
    @classmethod
    def validate_sprint_winner(cls, v, info):
        if 'race_weekend_id' in info.data and v is not None and v <= 0:
            raise ValueError('Sprint winner driver number must be positive')
        return v

class PredictionResponse(BaseModel):
    id: int
    user_id: int
    race_weekend_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    top_10_prediction: str
    pole_position: int
    sprint_winner: Optional[int]
    most_pit_stops_driver: int
    fastest_lap_driver: int
    most_positions_gained: int
    
    model_config = {
        "from_attributes": True
    }

class PredictionScoreResponse(BaseModel):
    id: int
    prediction_id: int
    calculated_at: datetime
    top_5_score: int
    position_6_to_10_score: int
    perfect_top_10_bonus: int
    partial_position_score: int
    pole_position_score: int
    sprint_winner_score: int
    most_pit_stops_score: int
    fastest_lap_score: int
    most_positions_gained_score: int
    streak_bonus: int
    underdog_bonus: int
    total_score: int
    
    model_config = {
        "from_attributes": True
    } 