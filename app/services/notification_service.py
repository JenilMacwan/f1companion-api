"""
Notification service for Firebase Cloud Messaging (FCM).
"""

from firebase_admin import messaging
from typing import Dict, Any

def send_topic_notification(topic: str, title: str, body: str, data: Dict[str, str] = None) -> bool:
    """
    Sends an FCM push notification to all users subscribed to a specific topic.
    """
    try:
        # Define the message payload
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data if data else {},
            topic=topic,
        )

        # Send a message to the devices subscribed to the provided topic.
        response = messaging.send(message)
        print(f"Successfully sent message to topic {topic}: {response}")
        return True
        
    except Exception as e:
        print(f"Error sending topic notification: {e}")
        return False

def evaluate_and_notify_major_event(message_data: Dict[str, Any]):
    """
    Evaluates a race control message and sends a push notification if it's a major event.
    """
    flag = message_data.get("flag")
    category = message_data.get("category")
    msg_text = message_data.get("message", "")
    
    topic = "race_events"
    title = None
    body = None

    if flag == "RED":
        title = "🔴 Red Flag"
        body = "Session has been suspended!"
    elif category == "SafetyCar":
        title = "🟡 Safety Car Deployed"
        body = "The Safety Car has been deployed."
    elif flag == "YELLOW" and "DOUBLE" in msg_text.upper():
        title = "🟡 Double Yellow Flags"
        body = msg_text
    
    # If it's a major event we identified, send the notification
    if title and body:
        send_topic_notification(
            topic=topic,
            title=title,
            body=body,
            data={"category": str(category), "flag": str(flag)}
        )
