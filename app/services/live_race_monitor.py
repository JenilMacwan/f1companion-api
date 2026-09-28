"""
Background monitor for live race control updates.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from app.services.race_control_service import get_race_control_messages
from app.core.websocket_manager import websocket_manager
from app.services.notification_service import evaluate_and_notify_major_event

# Store the number of messages seen so far for the "latest" session
# so we only broadcast and notify for truly new ones.
_seen_messages_count = None

async def start_live_monitoring(poll_interval_seconds: int = 2):
    """
    Background loop that continuously polls the in-memory race control
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
            
            # Initialize on first run to avoid spamming old messages
            if _seen_messages_count is None:
                _seen_messages_count = current_count
                
            # If session changed, message count likely resets or drops
            elif current_count < _seen_messages_count:
                _seen_messages_count = 0
            
            # 2. Check if there are new messages
            if current_count > _seen_messages_count:
                # We have new messages!
                new_messages = messages[_seen_messages_count:]
                
                # 3. Process each new message
                for msg in new_messages:
                    # Check if the message is recent (e.g., within the last 15 minutes)
                    # This prevents spamming notifications for old events when a session changes or restarts
                    is_recent = True
                    timestamp_str = msg.get("timestamp")
                    if timestamp_str:
                        try:
                            # Replace 'Z' with '+00:00' because datetime.fromisoformat in older python versions doesn't support 'Z'
                            parsed_str = timestamp_str.replace('Z', '+00:00')
                            # Parse ISO timestamp like '2026-08-23T15:08:13+00:00'
                            msg_time = datetime.fromisoformat(parsed_str)
                            if msg_time.tzinfo is None:
                                msg_time = msg_time.replace(tzinfo=timezone.utc)
                                
                            now = datetime.now(timezone.utc)
                            # Reduce window to 2 minutes to ensure we don't send notifications 
                            # if F1 starts streaming a replay of a recently ended session.
                            if now - msg_time > timedelta(minutes=2):
                                is_recent = False
                        except Exception as e:
                            print(f"Could not parse timestamp {timestamp_str}: {e}")

                    print(f"New Race Control Event: {msg.get('category')} - {msg.get('message')}")
                    
                    # a. Broadcast to all active WebSocket clients (Live Dashboards)
                    await websocket_manager.broadcast_json({"type": "race_control", "data": msg})
                    
                    # b. Evaluate for push notifications (FCM)
                    if is_recent:
                        evaluate_and_notify_major_event(msg)
                    else:
                        print("Skipping push notification for old event.")
                
                # 4. Update the seen count
                _seen_messages_count = current_count
                
        except Exception as e:
            print(f"Error in live race monitor loop: {e}")
            if "429" in str(e) or "401" in str(e):
                print("Rate limit or IP ban detected. Backing off for 1 hour...")
                await asyncio.sleep(3600)
                continue
            
        # 5. Sleep for the poll interval. We are reading from memory, so no API limits.
        await asyncio.sleep(poll_interval_seconds)
