from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import base64

from ..models.league import League
from ..models.user import User
from ..models.prediction import PredictionScore
from ..schemas.league import LeagueCreate, LeagueStanding, LeagueStandingsResponse

class LeagueService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_league(self, league: LeagueCreate, owner_id: int) -> League:
        """Create a new league and add the owner as first member."""
        icon_data = None
        if league.icon:
            try:
                icon_data = base64.b64decode(league.icon)
            except Exception:
                raise ValueError("Invalid icon format. Must be base64 encoded.")
        
        db_league = League(
            name=league.name,
            icon=icon_data,
            owner_id=owner_id
        )
        
        self.db.add(db_league)
        self.db.commit()
        self.db.refresh(db_league)
        
        # Add owner as first member
        db_league.members.append(self.db.query(User).get(owner_id))
        self.db.commit()
        
        return db_league
    
    def get_league(self, league_id: int) -> Optional[League]:
        """Get league by ID."""
        return self.db.query(League).filter(League.id == league_id).first()
    
    def get_user_leagues(self, user_id: int) -> List[League]:
        """Get all leagues a user is a member of."""
        user = self.db.query(User).get(user_id)
        return user.leagues if user else []
    
    def add_member(self, league_id: int, user_id: int) -> bool:
        """Add a user to a league."""
        league = self.get_league(league_id)
        user = self.db.query(User).get(user_id)
        
        if not league or not user:
            return False
            
        if user in league.members:
            return True
            
        league.members.append(user)
        self.db.commit()
        return True
    
    def remove_member(self, league_id: int, user_id: int, removed_by_id: int) -> bool:
        """Remove a user from a league. Only the owner can remove members."""
        league = self.get_league(league_id)
        
        if not league or (league.owner_id != removed_by_id).scalar():
            return False
            
        if (league.owner_id == user_id).scalar():
            return False  # Can't remove the owner
            
        user = self.db.query(User).get(user_id)
        if user in league.members:
            league.members.remove(user)
            self.db.commit()
            return True
            
        return False
    
    def get_standings(self, league_id: int) -> LeagueStandingsResponse:
        """Calculate current standings for a league."""
        league = self.get_league(league_id)
        if not league:
            raise ValueError("League not found")
            
        standings = []
        for member in league.members:
            # Get total points from prediction scores
            scores = self.db.query(PredictionScore)\
                .join(PredictionScore.prediction)\
                .filter(PredictionScore.prediction.has(user_id=member.id))\
                .all()
                
            total_points = sum(score.total_score.scalar() for score in scores)
            perfect_predictions = len([s for s in scores if (s.perfect_top_10_bonus > 0).scalar()])
            
            standings.append(LeagueStanding(
                user_id=member.id.scalar(),
                username=member.username.scalar(),
                total_points=total_points,
                predictions_made=len(scores),
                perfect_predictions=perfect_predictions,
                position=0  # Will be set after sorting
            ))
        
        # Sort by total points and assign positions
        standings.sort(key=lambda x: x.total_points, reverse=True)
        for i, standing in enumerate(standings, 1):
            standing.position = i
        
        return LeagueStandingsResponse(
            league_id=league.id.scalar(),
            league_name=league.name.scalar(),
            standings=standings,
            last_updated=datetime.utcnow()
        ) 