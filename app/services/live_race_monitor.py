"""
Background monitor for live race control updates.
"""

import asyncio
from app.services.race_control_service import get_race_control_messages
from app.core.websocket_manager import websocket_manager
from app.services.notification_service import evaluate_and_notify_major_event

# Store the number of messages seen so far for the "latest" session
# so we only broadcast and notify for truly new ones.
_seen_messages_count = 0

async def start_live_monitoring(poll_interval_seconds: int = 15):
    """
    Background loop that continuously polls OpenF1 for new race control
    messages for the "latest" session.
    """
    global _seen_messages_count
    print(f"Starting live race monitor. Polling every {poll_interval_seconds} seconds...")

    while True:
        try:
            # 1. Fetch latest race control messages
            data = get_race_control_messages(session_key="latest")
            
            messages = data.get("messages", [])
            current_count = len(messages)
            
            # 2. Check if there are new messages
            if current_count > _seen_messages_count:
                # We have new messages!
                new_messages = messages[_seen_messages_count:]
                
                # 3. Process each new message
                for msg in new_messages:
                    print(f"New Race Control Event: {msg.get('category')} - {msg.get('message')}")
                    
                    # a. Broadcast to all active WebSocket clients (Live Dashboards)
                    await websocket_manager.broadcast_json({"type": "race_control", "data": msg})
                    
                    # b. Evaluate for push notifications (FCM)
                    evaluate_and_notify_major_event(msg)
                
                # 4. Update the seen count
                _seen_messages_count = current_count
                
        except Exception as e:
            print(f"Error in live race monitor loop: {e}")
            
        # 5. Wait before polling again
        await asyncio.sleep(poll_interval_seconds)
