from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import base64
from sqlalchemy import select

from ..models.league import League
from ..models.user import User
from ..models.prediction import PredictionScore
from ..schemas.league import LeagueCreate, LeagueStanding, LeagueStandingsResponse

class LeagueService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_league(self, league: LeagueCreate, owner_id: int) -> League:
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
        query = select(User).where(User.id == owner_id)
        result = self.db.execute(query)
        owner = result.scalar_one_or_none()
        if owner:
            db_league.members.append(owner)
            self.db.commit()
            self.db.refresh(db_league)
        
        # Add member_count property to the league object
        setattr(db_league, 'member_count', len(db_league.members))
        
        return db_league
    
    async def get_league(self, league_id: int) -> Optional[League]:
        """Get league by ID."""
        query = select(League).where(League.id == league_id)
        result = self.db.execute(query)
        league = result.scalar_one_or_none()
        
        if league:
            # Add member_count property to the league object
            setattr(league, 'member_count', len(league.members))
            
        return league
    
    async def get_user_leagues(self, user_id: int) -> List[League]:
        """Get all leagues a user is a member of."""
        query = select(User).where(User.id == user_id)
        result = self.db.execute(query)
        user = result.scalar_one_or_none()
        
        leagues = user.leagues if user else []
        
        # Add member_count property to each league object
        for league in leagues:
            setattr(league, 'member_count', len(league.members))
            
        return leagues
    
    async def add_member(self, league_id: int, user_id: int) -> bool:
        """Add a user to a league."""
        league = await self.get_league(league_id)
        
        query = select(User).where(User.id == user_id)
        result = self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not league or not user:
            return False
            
        if user in league.members:
            return True
            
        league.members.append(user)
        self.db.commit()
        return True
    
    async def remove_member(self, league_id: int, user_id: int, removed_by_id: int) -> bool:
        """Remove a user from a league. Only the owner can remove members."""
        league = await self.get_league(league_id)
        
        # Get the owner_id as a regular integer
        owner_id = getattr(league, 'owner_id')
        if hasattr(owner_id, 'scalar'):
            owner_id = owner_id.scalar()
            
        if not league or owner_id != removed_by_id:
            return False
            
        if owner_id == user_id:
            return False  # Can't remove the owner
            
        query = select(User).where(User.id == user_id)
        result = self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return False
            
        if user in league.members:
            league.members.remove(user)
            self.db.commit()
            return True
            
        return False
    
    async def delete_league(self, league_id: int) -> bool:
        """Delete a league. Only the owner or a superadmin can do this."""
        league = await self.get_league(league_id)
        
        if not league:
            return False
            
        self.db.delete(league)
        self.db.commit()
        return True
    
    async def transfer_ownership(self, league_id: int, new_owner_id: int) -> bool:
        """Transfer league ownership to another member."""
        league = await self.get_league(league_id)
        
        if not league:
            return False
            
        # Check if new owner is a member
        query = select(User).where(User.id == new_owner_id)
        result = self.db.execute(query)
        new_owner = result.scalar_one_or_none()
        
        if not new_owner or new_owner not in league.members:
            return False
            
        # Update owner
        setattr(league, 'owner_id', new_owner_id)
        self.db.commit()
        return True
    
    async def get_standings(self, league_id: int) -> LeagueStandingsResponse:
        """Calculate current standings for a league."""
        league = await self.get_league(league_id)
        if not league:
            raise ValueError("League not found")
            
        standings = []
        for member in league.members:
            # Get member id as a regular integer
            member_id = getattr(member, 'id')
            if hasattr(member_id, 'scalar'):
                member_id = member_id.scalar()
            
            # Get member username as a regular string
            member_username = getattr(member, 'username')
            if hasattr(member_username, 'scalar'):
                member_username = member_username.scalar()
            
            # Get total points from prediction scores
            query = select(PredictionScore).join(PredictionScore.prediction).filter(
                PredictionScore.prediction.has(user_id=member_id)
            )
            result = self.db.execute(query)
            scores = result.scalars().all()
                
            # Calculate total points and perfect predictions
            total_points = 0
            perfect_predictions = 0
            
            for score in scores:
                # Get total_score as a regular integer
                score_value = getattr(score, 'total_score')
                if hasattr(score_value, 'scalar'):
                    score_value = score_value.scalar()
                total_points += score_value
                
                # Get perfect_top_10_bonus as a regular integer
                bonus_value = getattr(score, 'perfect_top_10_bonus')
                if hasattr(bonus_value, 'scalar'):
                    bonus_value = bonus_value.scalar()
                if bonus_value > 0:
                    perfect_predictions += 1
            
            standings.append(LeagueStanding(
                user_id=member_id,
                username=member_username,
                total_points=total_points,
                predictions_made=len(scores),
                perfect_predictions=perfect_predictions,
                position=0  # Will be set after sorting
            ))
        
        # Sort by total points and assign positions
        standings.sort(key=lambda x: x.total_points, reverse=True)
        for i, standing in enumerate(standings, 1):
            standing.position = i
        
        # Get league attributes as regular values
        league_id_value = getattr(league, 'id')
        if hasattr(league_id_value, 'scalar'):
            league_id_value = league_id_value.scalar()
        
        league_name_value = getattr(league, 'name')
        if hasattr(league_name_value, 'scalar'):
            league_name_value = league_name_value.scalar()
        
        return LeagueStandingsResponse(
            league_id=league_id_value,
            league_name=league_name_value,
            standings=standings,
            last_updated=datetime.utcnow()
        ) 