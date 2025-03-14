from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base

class UserPrediction(Base):
    __tablename__ = "user_predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    race_weekend_id = Column(Integer, ForeignKey("race_weekends.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Race finish predictions (stored as comma-separated driver numbers)
    top_10_prediction = Column(String, nullable=False)  # e.g., "1,44,11,4,55,63,16,81,23,77"
    pole_position = Column(Integer, nullable=False)  # Driver number
    sprint_winner = Column(Integer, nullable=True)  # Driver number, nullable for non-sprint weekends
    most_pit_stops_driver = Column(Integer, nullable=False)  # Driver with most pit stops
    fastest_lap_driver = Column(Integer, nullable=False)  # Driver number
    most_positions_gained = Column(Integer, nullable=False)  # Driver who will gain most positions
    
    # Relationships
    user = relationship("User", back_populates="predictions")
    race_weekend = relationship("RaceWeekend", back_populates="predictions")
    score = relationship("PredictionScore", back_populates="prediction", uselist=False)

class PredictionScore(Base):
    __tablename__ = "prediction_scores"

    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("user_predictions.id"), nullable=False)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Individual score components
    top_5_score = Column(Integer, default=0)  # 2 pts per correct driver
    position_6_to_10_score = Column(Integer, default=0)  # 3 pts per correct driver
    perfect_top_10_bonus = Column(Integer, default=0)  # 20 pts for perfect prediction
    partial_position_score = Column(Integer, default=0)  # 1 pt per correct position
    pole_position_score = Column(Integer, default=0)  # 5 pts
    sprint_winner_score = Column(Integer, default=0)  # 5 pts
    most_pit_stops_score = Column(Integer, default=0)  # 10 pts
    fastest_lap_score = Column(Integer, default=0)  # 10 pts
    most_positions_gained_score = Column(Integer, default=0)  # 10 pts
    streak_bonus = Column(Integer, default=0)  # Bonus for consecutive correct predictions
    underdog_bonus = Column(Integer, default=0)  # Bonus for correct underdog predictions
    
    total_score = Column(Integer, default=0)  # Sum of all scores
    
    # Relationship
    prediction = relationship("UserPrediction", back_populates="score") 