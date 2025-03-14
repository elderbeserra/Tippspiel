from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base

class RaceWeekend(Base):
    __tablename__ = "race_weekends"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer)
    round_number = Column(Integer)
    country = Column(String)
    location = Column(String)
    circuit_name = Column(String)
    session_date = Column(DateTime)
    has_sprint = Column(Boolean, default=False)
    
    # Relationships
    race_results = relationship("RaceResult", back_populates="race_weekend")
    qualifying_results = relationship("QualifyingResult", back_populates="race_weekend")
    sprint_results = relationship("SprintResult", back_populates="race_weekend")
    predictions = relationship("UserPrediction", back_populates="race_weekend")

class RaceResult(Base):
    __tablename__ = "race_results"

    id = Column(Integer, primary_key=True, index=True)
    race_weekend_id = Column(Integer, ForeignKey("race_weekends.id"), nullable=False)
    position = Column(Integer, nullable=False)
    driver_number = Column(Integer, nullable=False)
    driver_name = Column(String, nullable=False)
    team = Column(String, nullable=False)
    grid_position = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    points = Column(Float, nullable=False)
    fastest_lap = Column(Boolean, default=False)
    fastest_lap_time = Column(String, nullable=True)
    first_pit_lap = Column(Integer, nullable=True)  # Lap number of first pit stop
    first_pit_time = Column(String, nullable=True)  # Time of first pit stop (race time)
    pit_stops_count = Column(Integer, default=0)  # Total number of pit stops
    
    race_weekend = relationship("RaceWeekend", back_populates="race_results")

class QualifyingResult(Base):
    __tablename__ = "qualifying_results"

    id = Column(Integer, primary_key=True, index=True)
    race_weekend_id = Column(Integer, ForeignKey("race_weekends.id"))
    position = Column(Integer)
    driver_number = Column(Integer)
    driver_name = Column(String)
    team = Column(String)
    q1_time = Column(String)
    q2_time = Column(String)
    q3_time = Column(String)
    
    race_weekend = relationship("RaceWeekend", back_populates="qualifying_results")

class SprintResult(Base):
    __tablename__ = "sprint_results"

    id = Column(Integer, primary_key=True, index=True)
    race_weekend_id = Column(Integer, ForeignKey("race_weekends.id"))
    position = Column(Integer)
    driver_number = Column(Integer)
    driver_name = Column(String)
    team = Column(String)
    grid_position = Column(Integer)
    status = Column(String)
    points = Column(Float)
    
    race_weekend = relationship("RaceWeekend", back_populates="sprint_results") 