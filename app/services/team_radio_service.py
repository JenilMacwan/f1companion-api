"""
Team Radio service.

Fetches live and historical team radio communications
from the OpenF1 API and caches them in memory.
"""

import asyncio
from datetime import datetime
from app.core.config import OPENF1_BASE_URL
from app.core.http_client import http_client

# --- In-Memory Cache ---
_cached_team_radio = []
_cached_drivers_map = {}  # Maps lowercase last_name to driver_number
_cached_session_name = "Unknown Session"  # Stores the name of the current session (e.g., "Race")
_cached_event_name = "Unknown Event"      # Stores the Grand Prix name (e.g., "British Grand Prix")
_cached_round = None                      # Stores the championship round number if available

async def poll_team_radio_data(poll_interval_seconds: int = 15):
    """
    Background loop that continuously polls OpenF1 for the latest team radio data.
    """
    global _cached_team_radio, _cached_drivers_map
    global _cached_session_name, _cached_event_name, _cached_round
    
    print(f"Starting Team Radio monitor. Polling every {poll_interval_seconds} seconds...")

    _last_metadata_fetch = 0
    while True:
        try:
            session_key = "latest"
            
            current_time = asyncio.get_event_loop().time()
            # Fetch metadata only every 5 minutes (300 seconds) to save rate limits
            if current_time - _last_metadata_fetch > 300 or not _cached_drivers_map:
                _last_metadata_fetch = current_time
                
                # 1. Fetch Session Metadata (to get the session_name and meeting_key)
                session_url = f"{OPENF1_BASE_URL}/sessions?session_key={session_key}"
                session_data = await asyncio.to_thread(http_client.fetch_json, session_url)
                
                meeting_key = None
                if isinstance(session_data, list) and len(session_data) > 0:
                    session_obj = session_data[0]
                    _cached_session_name = session_obj.get("session_name", "Unknown Session")
                    meeting_key = session_obj.get("meeting_key")
                    
                # 2. Fetch Meeting Metadata (to get the event name and round number)
                if meeting_key:
                    meeting_url = f"{OPENF1_BASE_URL}/meetings?meeting_key={meeting_key}"
                    meeting_data = await asyncio.to_thread(http_client.fetch_json, meeting_url)
                    
                    if isinstance(meeting_data, list) and len(meeting_data) > 0:
                        meeting_obj = meeting_data[0]
                        _cached_event_name = meeting_obj.get("meeting_name", "Unknown Event")
                        _cached_round = meeting_obj.get("round_number") or meeting_obj.get("round")

                # 3. Fetch Drivers (to map last_name to driver_number)
                drivers_url = f"{OPENF1_BASE_URL}/drivers?session_key={session_key}"
                drivers_data = await asyncio.to_thread(http_client.fetch_json, drivers_url)
                
                if isinstance(drivers_data, list):
                    new_map = {}
                    for driver in drivers_data:
                        if driver.get("last_name") and driver.get("driver_number") is not None:
                            new_map[driver["last_name"].lower()] = driver["driver_number"]
                    _cached_drivers_map = new_map

            # 4. Fetch all Team Radios for the session
            url = f"{OPENF1_BASE_URL}/team_radio?session_key={session_key}"
            data = await asyncio.to_thread(http_client.fetch_json, url)
            
            if not isinstance(data, list):
                data = []

            clean_messages = []
            for msg in data:
                clean_messages.append({
                    "timestamp": msg.get("date"),
                    "driver_number": msg.get("driver_number"),
                    "recording_url": msg.get("recording_url"),
                    "session_key": msg.get("session_key")
                })

            # Sort messages by timestamp descending (newest first)
            clean_messages.sort(key=lambda x: x["timestamp"] if x["timestamp"] else "", reverse=True)
            
            # Update cache safely
            _cached_team_radio = clean_messages

        except Exception as e:
            print(f"Error in team radio monitor loop: {e}")
            if "429" in str(e) or "401" in str(e):
                print("Rate limit or IP ban detected. Backing off for 1 hour...")
                await asyncio.sleep(3600)
                continue
            
        await asyncio.sleep(poll_interval_seconds)


def get_team_radio_messages(session_key: str = "latest", last_name: str = None):
    """
    Return team radio messages from the server's in-memory cache.
    
    Args:
        session_key (str): The session key (currently only "latest" is actively cached).
        last_name (str, optional): Filter by driver's last name.
        
    Returns:
        Dict with event/session info, total messages count and the messages list.
    """
    global _cached_team_radio, _cached_drivers_map 
    global _cached_session_name, _cached_event_name, _cached_round

    filtered_messages = _cached_team_radio

    if last_name:
        last_name_lower = last_name.lower()
        target_driver_number = _cached_drivers_map.get(last_name_lower)
        
        # If we couldn't resolve the driver, return empty early
        if target_driver_number is None:
            return {
                "session_key": session_key,
                "session_name": _cached_session_name,
                "event_name": _cached_event_name,
                "round": _cached_round,
                "last_name": last_name,
                "total_messages": 0,
                "messages": []
            }
            
        # Filter the cached list by the driver_number
        filtered_messages = [msg for msg in _cached_team_radio if msg.get("driver_number") == target_driver_number]

    return {
        "session_key": session_key,
        "session_name": _cached_session_name,
        "event_name": _cached_event_name,
        "round": _cached_round,
        "last_name": last_name,
        "total_messages": len(filtered_messages),
        "messages": filtered_messages
    }