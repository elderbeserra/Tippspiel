from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
from .user import league_members

class League(Base):
    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    icon = Column(LargeBinary, nullable=True)  # Store icon as binary data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="owned_leagues")
    members = relationship(
        "User",
        secondary=league_members,
        back_populates="leagues"
    )
    
    # League standings will be calculated dynamically based on member predictions 