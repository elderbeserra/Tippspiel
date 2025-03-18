from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import List, Dict, Any, Optional, Sequence
from datetime import datetime, timedelta
import logging
import os
import sqlite3

from ..models.user import User
from ..models.league import League
from ..models.prediction import UserPrediction, PredictionScore
from ..models.f1_data import RaceWeekend, RaceResult
from ..core.config import settings

logger = logging.getLogger(__name__)

class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> Sequence[User]:
        """Get all users with pagination."""
        query = select(User).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_user_count(self) -> int:
        """Get total number of users."""
        query = select(func.count(User.id))
        result = await self.db.execute(query)
        return result.scalar_one()
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_user_role(self, user_id: int, is_admin: bool, is_superadmin: bool = False) -> bool:
        """Update user role (admin and superadmin status)."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Use setattr for SQLAlchemy models
        setattr(user, 'is_admin', is_admin)
        setattr(user, 'is_superadmin', is_superadmin)
        await self.db.commit()
        return True
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete a user and all associated data."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Delete user's predictions
        query = select(UserPrediction).where(UserPrediction.user_id == user_id)
        result = await self.db.execute(query)
        predictions = result.scalars().all()
        
        for prediction in predictions:
            # Delete prediction scores
            query = select(PredictionScore).where(PredictionScore.prediction_id == prediction.id)
            result = await self.db.execute(query)
            scores = result.scalars().all()
            for score in scores:
                await self.db.delete(score)
            
            await self.db.delete(prediction)
        
        # Remove user from leagues (but don't delete leagues they own)
        query = select(League).where(League.owner_id == user_id)
        result = await self.db.execute(query)
        owned_leagues = result.scalars().all()
        
        for league in owned_leagues:
            # Transfer ownership to another member or delete if no other members
            if league.members and len(league.members) > 1:
                for member in league.members:
                    if member.id != user_id:
                        setattr(league, 'owner_id', member.id)
                        break
            else:
                await self.db.delete(league)
        
        # Delete the user
        await self.db.delete(user)
        await self.db.commit()
        return True
    
    async def get_all_leagues(self, skip: int = 0, limit: int = 100) -> Sequence[League]:
        """Get all leagues with pagination."""
        query = select(League).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_league_count(self) -> int:
        """Get total number of leagues."""
        query = select(func.count(League.id))
        result = await self.db.execute(query)
        return result.scalar_one()
    
    async def delete_league(self, league_id: int) -> bool:
        """Delete a league."""
        query = select(League).where(League.id == league_id)
        result = await self.db.execute(query)
        league = result.scalar_one_or_none()
        
        if not league:
            return False
        
        await self.db.delete(league)
        await self.db.commit()
        return True
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        # Get database stats
        db_path = settings.SQLITE_URL.replace("sqlite:///", "")
        db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
        
        # Get counts
        user_count = await self.get_user_count()
        league_count = await self.get_league_count()
        
        query = select(func.count(UserPrediction.id))
        result = await self.db.execute(query)
        prediction_count = result.scalar_one()
        
        query = select(func.count(RaceWeekend.id))
        result = await self.db.execute(query)
        race_weekend_count = result.scalar_one()
        
        # Get recent activity
        one_week_ago = datetime.now() - timedelta(days=7)
        
        query = select(func.count(User.id)).where(User.created_at >= one_week_ago)
        result = await self.db.execute(query)
        new_users_count = result.scalar_one()
        
        query = select(func.count(UserPrediction.id)).where(UserPrediction.created_at >= one_week_ago)
        result = await self.db.execute(query)
        new_predictions_count = result.scalar_one()
        
        return {
            "database_size_mb": round(db_size / (1024 * 1024), 2),
            "user_count": user_count,
            "league_count": league_count,
            "prediction_count": prediction_count,
            "race_weekend_count": race_weekend_count,
            "new_users_last_week": new_users_count,
            "new_predictions_last_week": new_predictions_count,
            "timestamp": datetime.now()
        }
    
    async def run_database_maintenance(self) -> Dict[str, Any]:
        """Run database maintenance tasks."""
        try:
            # Connect directly to SQLite for maintenance operations
            db_path = settings.SQLITE_URL.replace("sqlite:///", "")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Run VACUUM to rebuild the database file
            cursor.execute("VACUUM")
            
            # Run integrity check
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            
            # Get database stats
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            
            # Calculate database size
            db_size = page_count * page_size
            
            conn.close()
            
            return {
                "success": True,
                "integrity_check": integrity_result,
                "database_size_mb": round(db_size / (1024 * 1024), 2),
                "timestamp": datetime.now()
            }
        except Exception as e:
            logger.error(f"Error during database maintenance: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now()
            }
    
    async def correct_race_result(self, race_result_id: int, position: int, driver_number: int) -> bool:
        """Correct a race result (for data corrections)."""
        query = select(RaceResult).where(RaceResult.id == race_result_id)
        result = await self.db.execute(query)
        race_result = result.scalar_one_or_none()
        
        if not race_result:
            return False
        
        # Use setattr for SQLAlchemy models
        setattr(race_result, 'position', position)
        setattr(race_result, 'driver_number', driver_number)
        
        await self.db.commit()
        
        # Get the race_weekend_id as a regular integer
        race_weekend_id = getattr(race_result, 'race_weekend_id')
        if hasattr(race_weekend_id, 'scalar'):
            race_weekend_id = race_weekend_id.scalar()
        
        # Recalculate scores for affected predictions
        await self._recalculate_scores_for_race(race_weekend_id)
        
        return True
    
    async def _recalculate_scores_for_race(self, race_weekend_id: int) -> None:
        """Recalculate scores for all predictions for a specific race weekend."""
        # Get all predictions for this race weekend
        query = select(UserPrediction).where(UserPrediction.race_weekend_id == race_weekend_id)
        result = await self.db.execute(query)
        predictions = result.scalars().all()
        
        # Get race results
        query = select(RaceResult).where(RaceResult.race_weekend_id == race_weekend_id)
        result = await self.db.execute(query)
        race_results = result.scalars().all()
        
        # Import here to avoid circular imports
        from .scoring_service import ScoringService
        scoring_service = ScoringService(self.db)
        
        # Recalculate scores for each prediction
        for prediction in predictions:
            # Delete existing score
            query = select(PredictionScore).where(PredictionScore.prediction_id == prediction.id)
            result = await self.db.execute(query)
            existing_score = result.scalar_one_or_none()
            
            if existing_score:
                await self.db.delete(existing_score)
            
            # Calculate new score
            new_score = scoring_service.calculate_score(prediction, race_results)
            
            # Save new score
            self.db.add(new_score)
        
        await self.db.commit() 