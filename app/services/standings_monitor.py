"""
Background monitor for championship standings updates.
"""

import asyncio
from app.services.standings_service import get_driver_standings
from app.services.notification_service import notify_standings_update

_last_top_points = None

async def start_standings_monitoring(interval_hours: int = 2):
    """
    Background loop that polls Jolpica Ergast for standings updates.
    """
    global _last_top_points
    interval_seconds = interval_hours * 3600
    print(f"Starting standings monitor. Polling every {interval_hours} hours...")

    while True:
        try:
            # 1. Fetch latest standings
            standings_data = get_driver_standings()
            drivers = standings_data.get("drivers", [])
            
            if drivers:
                # 2. Get the current leader
                leader = drivers[0]
                current_points = leader.get("points")
                
                # Initialize on first run without notifying
                if _last_top_points is None:
                    _last_top_points = current_points
                
                # 3. Check if points have changed since last check (meaning a race happened)
                elif current_points != _last_top_points:
                    print(f"Standings updated! New leader points: {current_points}")
                    notify_standings_update(leader)
                    _last_top_points = current_points
                
        except Exception as e:
            print(f"Error in standings monitor loop: {e}")
            
        # 4. Wait before polling again
        await asyncio.sleep(interval_seconds)
