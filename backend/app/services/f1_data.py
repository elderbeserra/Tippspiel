import fastf1
from fastf1.core import Session
from typing import Dict, List, Optional
import logging
import pandas as pd

logger = logging.getLogger(__name__)

class F1DataService:
    def __init__(self):
        # Enable caching
        fastf1.Cache.enable_cache('backend/.cache')
        
    async def get_race_schedule(self, year: int) -> List[Dict]:
        """Get the F1 race schedule for a specific year."""
        try:
            schedule = fastf1.get_event_schedule(year)
            return schedule.to_dict('records')
        except Exception as e:
            logger.error(f"Error fetching race schedule for {year}: {str(e)}")
            return []

    async def get_race_results(self, year: int, round_number: int) -> Dict:
        """Get race results including pit stop information."""
        try:
            session = fastf1.get_session(year, round_number, 'R')
            session.load()
            
            # Get race results
            results = session.results
            
            # Get pit stop data
            laps = session.laps
            pit_stops = {}
            
            for driver in results.index:
                driver_number = results.at[driver, 'DriverNumber']
                driver_laps = laps.pick_driver(int(driver_number))
                pit_laps = driver_laps[driver_laps['PitOutTime'].notna()]
                
                if not pit_laps.empty:
                    first_pit = pit_laps.iloc[0]
                    pit_stops[driver_number] = {
                        'first_pit_lap': int(first_pit['LapNumber']),  # Lap number
                        'first_pit_time': str(first_pit['LapTime']),  # Lap time when pit occurred
                        'pit_stops_count': len(pit_laps)
                    }
                else:
                    pit_stops[driver_number] = {
                        'first_pit_lap': None,
                        'first_pit_time': None,
                        'pit_stops_count': 0
                    }
            
            # Convert results to list of dictionaries
            race_results = []
            for idx in results.index:
                driver_number = results.loc[idx, 'DriverNumber']
                pit_data = pit_stops.get(driver_number, {
                    'first_pit_lap': None,
                    'first_pit_time': None,
                    'pit_stops_count': 0
                })
                
                race_results.append({
                    'Position': results.loc[idx, 'Position'],
                    'DriverNumber': driver_number,
                    'DriverName': f"{results.loc[idx, 'FirstName']} {results.loc[idx, 'LastName']}",
                    'Team': results.loc[idx, 'TeamName'],
                    'GridPosition': results.loc[idx, 'GridPosition'],
                    'Status': results.loc[idx, 'Status'],
                    'Points': results.loc[idx, 'Points'],
                    'FastestLap': results.loc[idx, 'FastestLap'],
                    'FastestLapTime': str(results.loc[idx, 'FastestLapTime']) if pd.notna(results.loc[idx, 'FastestLapTime']) else None,
                    'FirstPitLap': pit_data['first_pit_lap'],
                    'FirstPitTime': pit_data['first_pit_time'],
                    'PitStopsCount': pit_data['pit_stops_count']
                })
            
            return {'race_results': race_results}
        except Exception as e:
            logger.error(f"Error fetching race results for {year} round {round_number}: {str(e)}")
            return {}

    async def get_qualifying_results(self, year: int, round_number: int) -> List[Dict]:
        """Get qualifying session results."""
        try:
            session = fastf1.get_session(year, round_number, 'Q')
            session.load()
            return session.results.to_dict('records')
        except Exception as e:
            logger.error(f"Error fetching qualifying results for {year} round {round_number}: {str(e)}")
            return []

    async def get_sprint_results(self, year: int, round_number: int) -> Optional[List[Dict]]:
        """Get sprint race results if available."""
        try:
            session = fastf1.get_session(year, round_number, 'S')
            session.load()
            return session.results.to_dict('records')
        except Exception as e:
            logger.error(f"Error fetching sprint results for {year} round {round_number}: {str(e)}")
            return None

    def _get_fastest_lap(self, session: Session) -> Dict:
        """Extract fastest lap information from session."""
        try:
            laps = session.laps
            fastest_lap = laps.pick_fastest()
            return {
                'driver': fastest_lap['Driver'],
                'time': str(fastest_lap['LapTime']),
                'lap_number': fastest_lap['LapNumber'],
                'speed': fastest_lap['SpeedI2']
            }
        except Exception as e:
            logger.error(f"Error extracting fastest lap: {str(e)}")
            return {} 