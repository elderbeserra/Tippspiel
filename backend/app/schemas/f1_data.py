from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class RaceResultBase(BaseModel):
    position: int
    driver_number: int
    driver_name: str
    team: str
    grid_position: int
    status: str
    points: float
    fastest_lap: bool
    fastest_lap_time: Optional[str]

    class Config:
        from_attributes = True

class QualifyingResultBase(BaseModel):
    position: int
    driver_number: int
    driver_name: str
    team: str
    q1_time: Optional[str]
    q2_time: Optional[str]
    q3_time: Optional[str]

    class Config:
        from_attributes = True

class SprintResultBase(BaseModel):
    position: int
    driver_number: int
    driver_name: str
    team: str
    grid_position: int
    status: str
    points: float

    class Config:
        from_attributes = True

class RaceWeekendBase(BaseModel):
    year: int
    round_number: int
    country: str
    location: str
    circuit_name: str
    session_date: datetime
    has_sprint: bool

class RaceWeekend(RaceWeekendBase):
    id: int
    race_results: List[RaceResultBase] = []
    qualifying_results: List[QualifyingResultBase] = []
    sprint_results: List[SprintResultBase] = []

    class Config:
        from_attributes = True

class RaceWeekendList(BaseModel):
    items: List[RaceWeekend]
    total: int 