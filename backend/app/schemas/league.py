from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
import base64

class LeagueBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)

class LeagueCreate(LeagueBase):
    icon: Optional[str] = Field(None, description="Base64 encoded image data")
    
    @field_validator('icon')
    @classmethod
    def validate_icon(cls, v):
        if v:
            try:
                base64.b64decode(v)
            except Exception:
                raise ValueError("Invalid icon format. Must be base64 encoded.")
        return v

class LeagueResponse(LeagueBase):
    id: int
    created_at: datetime
    owner_id: int
    icon: Optional[str] = None  # Will be returned as base64
    member_count: int
    
    model_config = {
        "from_attributes": True
    }

class LeagueStanding(BaseModel):
    user_id: int
    username: str
    total_points: int
    position: int
    predictions_made: int
    perfect_predictions: int

class LeagueStandingsResponse(BaseModel):
    league_id: int
    league_name: str
    standings: List[LeagueStanding]
    last_updated: datetime

class LeagueMemberResponse(BaseModel):
    user_id: int
    username: str
    joined_at: datetime
    is_owner: bool 