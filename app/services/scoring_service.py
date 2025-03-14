def _get_most_pit_stops_driver(self, race_results: List[RaceResult]) -> Optional[int]:
    """Get the driver number who made the most pit stops during the race."""
    if not race_results:
        return None

    sorted_results = sorted(race_results, key=lambda x: x.pit_stops_count, reverse=True)
    return sorted_results[0].driver_number if sorted_results else None

def _get_most_positions_gained_driver(self, race_results: List[RaceResult]) -> Optional[int]:
    """Get the driver number who gained the most positions during the race."""
    if not race_results:
        return None

    # Calculate positions gained (grid position - final position)
    position_changes = [(r.driver_number, r.grid_position - r.position) for r in race_results]
    if not position_changes:
        return None

    # Return driver number with highest position gain
    return max(position_changes, key=lambda x: x[1])[0]