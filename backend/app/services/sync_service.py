from sqlalchemy.orm import Session
from typing import List, Dict
import logging
from .f1_data import F1DataService
from ..models.f1_data import RaceWeekend, RaceResult, QualifyingResult, SprintResult

logger = logging.getLogger(__name__)

class F1SyncService:
    def __init__(self, db: Session):
        self.db = db
        self.f1_service = F1DataService()

    async def sync_race_schedule(self, year: int) -> List[RaceWeekend]:
        """Synchronize race schedule for a specific year."""
        try:
            schedule = await self.f1_service.get_race_schedule(year)
            race_weekends = []

            for event in schedule:
                race_weekend = RaceWeekend(
                    year=year,
                    round_number=event.get('RoundNumber'),
                    country=event.get('Country'),
                    location=event.get('Location'),
                    circuit_name=event.get('CircuitName'),
                    session_date=event.get('EventDate'),
                    has_sprint=event.get('Sprint', False)
                )
                
                existing = self.db.query(RaceWeekend).filter(
                    RaceWeekend.year == year,
                    RaceWeekend.round_number == event.get('RoundNumber')
                ).first()

                if not existing:
                    self.db.add(race_weekend)
                    race_weekends.append(race_weekend)
                else:
                    # Update existing record
                    for key, value in event.items():
                        setattr(existing, key.lower(), value)
                    race_weekends.append(existing)

            self.db.commit()
            return race_weekends

        except Exception as e:
            logger.error(f"Error syncing race schedule for {year}: {str(e)}")
            self.db.rollback()
            return []

    async def sync_race_results(self, race_weekend: RaceWeekend):
        """Synchronize all results for a specific race weekend."""
        try:
            # Get race results
            results = await self.f1_service.get_race_results(
                race_weekend.year.scalar(), 
                race_weekend.round_number.scalar()
            )

            if results.get('race_results'):
                await self._sync_race_results(race_weekend.id.scalar(), results['race_results'])
                
            # Get qualifying results
            quali_results = await self.f1_service.get_qualifying_results(
                race_weekend.year.scalar(), 
                race_weekend.round_number.scalar()
            )
            if quali_results:
                await self._sync_qualifying_results(race_weekend.id.scalar(), quali_results)

            # If it's a sprint weekend, get sprint results
            if race_weekend.has_sprint.scalar():
                sprint_results = await self.f1_service.get_sprint_results(
                    race_weekend.year.scalar(), 
                    race_weekend.round_number.scalar()
                )
                if sprint_results:
                    await self._sync_sprint_results(race_weekend.id.scalar(), sprint_results)

            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Error syncing results for race {race_weekend.id}: {str(e)}")
            self.db.rollback()
            return False

    async def _sync_race_results(self, race_weekend_id: int, results: List[Dict]):
        """Sync race results for a specific race weekend."""
        for result in results:
            race_result = RaceResult(
                race_weekend_id=race_weekend_id,
                position=result.get('Position'),
                driver_number=result.get('DriverNumber'),
                driver_name=result.get('DriverName'),
                team=result.get('Team'),
                grid_position=result.get('GridPosition'),
                status=result.get('Status'),
                points=result.get('Points'),
                fastest_lap=result.get('FastestLap', False),
                fastest_lap_time=result.get('FastestLapTime')
            )

            existing = self.db.query(RaceResult).filter(
                RaceResult.race_weekend_id == race_weekend_id,
                RaceResult.driver_number == result.get('DriverNumber')
            ).first()

            if not existing:
                self.db.add(race_result)
            else:
                for key, value in result.items():
                    setattr(existing, key.lower(), value)

    async def _sync_qualifying_results(self, race_weekend_id: int, results: List[Dict]):
        """Sync qualifying results for a specific race weekend."""
        for result in results:
            quali_result = QualifyingResult(
                race_weekend_id=race_weekend_id,
                position=result.get('Position'),
                driver_number=result.get('DriverNumber'),
                driver_name=result.get('DriverName'),
                team=result.get('Team'),
                q1_time=result.get('Q1'),
                q2_time=result.get('Q2'),
                q3_time=result.get('Q3')
            )

            existing = self.db.query(QualifyingResult).filter(
                QualifyingResult.race_weekend_id == race_weekend_id,
                QualifyingResult.driver_number == result.get('DriverNumber')
            ).first()

            if not existing:
                self.db.add(quali_result)
            else:
                for key, value in result.items():
                    setattr(existing, key.lower(), value)

    async def _sync_sprint_results(self, race_weekend_id: int, results: List[Dict]):
        """Sync sprint results for a specific race weekend."""
        for result in results:
            sprint_result = SprintResult(
                race_weekend_id=race_weekend_id,
                position=result.get('Position'),
                driver_number=result.get('DriverNumber'),
                driver_name=result.get('DriverName'),
                team=result.get('Team'),
                grid_position=result.get('GridPosition'),
                status=result.get('Status'),
                points=result.get('Points')
            )

            existing = self.db.query(SprintResult).filter(
                SprintResult.race_weekend_id == race_weekend_id,
                SprintResult.driver_number == result.get('DriverNumber')
            ).first()

            if not existing:
                self.db.add(sprint_result)
            else:
                for key, value in result.items():
                    setattr(existing, key.lower(), value) 