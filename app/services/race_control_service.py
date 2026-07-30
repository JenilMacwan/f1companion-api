"""
Race Control service.

Fetches live and historical race control messages (flags, safety cars, investigations)
from the OpenF1 API.
"""

from app.core.config import OPENF1_BASE_URL
from app.core.http_client import http_client

def get_race_control_messages(session_key: str = "latest"):
    """
    Fetch race control messages for a specific session.
    
    Args:
        session_key (str): The session key (e.g., 'latest' or '9158').
        
    Returns:
        Dict with total messages count and the messages list.
    """
    url = f"{OPENF1_BASE_URL}/race_control?session_key={session_key}"
    data = http_client.fetch_json(url)
    
    # OpenF1 returns a list directly
    if not isinstance(data, list):
        data = []

    clean_messages = []
    for msg in data:
        # Format the timestamp for better readability if needed, or return as is
        clean_messages.append({
            "timestamp": msg.get("date"),
            "category": msg.get("category", "Other"),
            "message": msg.get("message", ""),
            "flag": msg.get("flag"),
            "driver_number": msg.get("driver_number"),
            "lap_number": msg.get("lap_number"),
            "scope": msg.get("scope"),
            "sector": msg.get("sector")
        })

    return {
        "session_key": session_key,
        "total_messages": len(clean_messages),
        "messages": clean_messages
    }
