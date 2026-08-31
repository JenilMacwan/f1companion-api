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
        payload_data = data if data else {}
        payload_data["title"] = title
        payload_data["body"] = body

        message = messaging.Message(
            data=payload_data,
            topic=topic,
        )
        
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
    
    topic = "live_race_events"
    title = None
    body = None

    if flag == "RED":
        title = "🔴 Red Flag"
        body = "Session has been suspended!"
    elif category == "SafetyCar":
        title = f"🟡 {msg_text}"
    elif flag == "YELLOW" and "DOUBLE" in msg_text.upper():
        title = "🟡 Double Yellow Flags"
        body = msg_text
    elif category == "SessionStatus":
        title = f"{msg_text}"
    
    # If it's a major event we identified, send the notification
    if title and body:
        send_topic_notification(
            topic=topic,
            title=title,
            body=body,
            data={"category": str(category), "flag": str(flag)}
        )

def notify_breaking_news(article: Dict[str, Any]):
    """
    Sends a push notification for breaking news.
    """
    topic = "breaking_news"
    title = article.get("title", "Breaking F1 News")
    
    # Create a short snippet for the body
    body = article.get("summary", "")
    if len(body) > 100:
        body = body[:97] + "..."
        
    data = {
        "url": article.get("link", "")
    }
    
    send_topic_notification(topic, title, body, data)

def notify_standings_update(top_driver: Dict[str, Any]):
    """
    Sends a push notification when championship standings are updated.
    """
    topic = "standings_updates"
    title = "🏁 Championship Standings Updated!"
    
    driver_name = top_driver.get("name", "Unknown Driver")
    points = top_driver.get("points", "0")
    
    body = f"{driver_name} leads the championship with {points} points."
    
    send_topic_notification(topic, title, body)

