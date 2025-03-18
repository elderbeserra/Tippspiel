from fastapi_utils.tasks import repeat_every
from ..core.database import SessionLocal
from ..services.sync_service import F1SyncService
from ..models.f1_data import RaceWeekend
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class F1DataSynchronizer:
    def __init__(self):
        self.db = SessionLocal()
        self.sync_service = F1SyncService(self.db)

    async def sync_current_season(self):
        """Synchronize data for the current F1 season."""
        try:
            current_year = datetime.now().year
            logger.info(f"Starting sync for {current_year} F1 season")
            
            # Sync race schedule
            race_weekends = await self.sync_service.sync_race_schedule(current_year)
            logger.info(f"Synced {len(race_weekends)} race weekends for {current_year}")

            # Sync results for completed race weekends
            for race_weekend in race_weekends:
                session_date = race_weekend.session_date
                if hasattr(session_date, 'scalar'):
                    session_date = session_date.scalar()
                if session_date <= datetime.now():
                    success = await self.sync_service.sync_race_results(race_weekend)
                    if success:
                        logger.info(f"Successfully synced results for {race_weekend.circuit_name}")
                    else:
                        logger.error(f"Failed to sync results for {race_weekend.circuit_name}")

        except Exception as e:
            logger.error(f"Error in F1 data sync: {str(e)}")
        finally:
            self.db.close()

    async def sync_race_results(self, race_weekend: RaceWeekend):
        """Synchronize results for a specific race weekend."""
        try:
            if race_weekend:
                current_time = datetime.now()
                session_date = race_weekend.session_date
                if hasattr(session_date, 'scalar'):
                    session_date = session_date.scalar()
                race_end = session_date + timedelta(hours=2)
                if current_time >= race_end + timedelta(hours=1):
                    success = await self.sync_service.sync_race_results(race_weekend)
                    if success:
                        logger.info(f"Successfully synced results for {race_weekend.circuit_name}")
                    else:
                        logger.error(f"Failed to sync results for {race_weekend.circuit_name}")
        except Exception as e:
            logger.error(f"Error in race results sync: {str(e)}")
        finally:
            self.db.close()

f1_synchronizer = F1DataSynchronizer()

@repeat_every(seconds=60)  # Check every minute for scheduling
async def schedule_sync():
    """Schedule synchronization based on specific days and times."""
    try:
        now = datetime.now()
        
        # Wednesday sync (every Wednesday at 12:00 PM)
        if now.weekday() == 2 and now.hour == 12 and now.minute == 0:
            await f1_synchronizer.sync_current_season()
            
        # Sunday post-race sync (check for races that ended within the last hour)
        if now.weekday() == 6:  # Sunday
            race_weekend = (
                f1_synchronizer.db.query(RaceWeekend)
                .filter(
                    RaceWeekend.year == now.year,
                    RaceWeekend.session_date <= now,
                    RaceWeekend.session_date >= now - timedelta(hours=2)
                )
                .first()
            )
            
            if race_weekend:
                session_date = race_weekend.session_date
                if hasattr(session_date, 'scalar'):
                    session_date = session_date.scalar()
                race_end = session_date + timedelta(hours=2)
                if now >= race_end + timedelta(hours=1):
                    await f1_synchronizer.sync_race_results(race_weekend)

    except Exception as e:
        logger.error(f"Error in sync scheduling: {str(e)}")
    finally:
        f1_synchronizer.db.close() 