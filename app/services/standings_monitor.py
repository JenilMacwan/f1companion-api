"""
Background monitor for championship standings updates.
"""

import asyncio
from app.services.standings_service import get_driver_standings
from app.services.notification_service import notify_standings_update

_last_standings_hash = None

async def start_standings_monitoring(interval_hours: int = 2):
    """
    Background loop that polls Jolpica Ergast for standings updates.
    """
    global _last_standings_hash
    interval_seconds = interval_hours * 3600
    print(f"Starting standings monitor. Polling every {interval_hours} hours...")

    while True:
        try:
            # 1. Fetch latest standings
            standings_data = get_driver_standings()
            drivers = standings_data.get("drivers", [])
            
            if drivers:
                # 2. Create a unique signature of the current points table
                # We concatenate all points so if ANY driver scores, the string changes.
                current_standings_hash = "-".join([str(d.get("points", "0")) for d in drivers])
                
                # Initialize on first run without notifying
                if _last_standings_hash is None:
                    _last_standings_hash = current_standings_hash
                
                # 3. Check if the table has changed since last check
                elif current_standings_hash != _last_standings_hash:
                    leader = drivers[0]
                    print(f"Standings updated! Leader: {leader.get('name')}")
                    notify_standings_update(leader)
                    _last_standings_hash = current_standings_hash
                
        except Exception as e:
            print(f"Error in standings monitor loop: {e}")
            
        # 4. Wait before polling again
        await asyncio.sleep(interval_seconds)
