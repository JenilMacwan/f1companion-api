"""
Race Control service.

Fetches live race control messages (flags, safety cars, investigations)
from the in-memory FastF1 live timing stream.
"""

from app.services.live_timing_service import live_timing_state, state_lock
from datetime import datetime, timezone

def is_important_message(msg: dict) -> bool:
    message_raw = msg.get("Message")
    message = str(message_raw).lower() if message_raw else ""
    
    flag_raw = msg.get("Flag")
    flag = str(flag_raw).upper() if flag_raw else ""
    
    category_raw = msg.get("Category")
    category = str(category_raw).lower() if category_raw else ""

    if flag in ["RED", "YELLOW", "DOUBLE YELLOW", "VSC", "SC"]:
        return True
        
    if category == "safetycar":
        return True

    if "session" in message:
        if any(w in message for w in ["start", "stop", "end", "resume"]):
            return True

    keywords = [
        "red flag",
        "yellow flag",
        "double yellow",
        "vsc",
        "virtual safety car",
        "safety car",
        "penalty"
    ]
    
    for kw in keywords:
        if kw in message:
            return True
            
    return False

def get_race_control_messages(session_key: str = "latest"):
    """
    Fetch race control messages from the in-memory live timing state.
    
    Args:
        session_key (str): The session key. Currently fetches from live memory.
        
    Returns:
        Dict with total messages count and the messages list.
    """
    with state_lock:
        # Create a shallow copy to iterate over
        raw_messages = list(live_timing_state.get("RaceControlMessages", []))

    clean_messages = []
    for msg in raw_messages:
        if not isinstance(msg, dict):
            continue
        if not is_important_message(msg):
            continue
            
        # FastF1 typical keys: Message, Category, Flag, RacingNumber, Lap, Scope, Sector, Utc
        timestamp = msg.get("Utc")
        if not timestamp:
            timestamp = datetime.now(timezone.utc).isoformat()
            
        clean_messages.append({
            "timestamp": timestamp,
            "category": msg.get("Category", "Other"),
            "message": msg.get("Message", ""),
            "flag": msg.get("Flag"),
            "driver_number": msg.get("RacingNumber"),
            "lap_number": msg.get("Lap"),
            "scope": msg.get("Scope"),
            "sector": msg.get("Sector")
        })

    return {
        "session_key": session_key,
        "total_messages": len(clean_messages),
        "messages": clean_messages
    }
