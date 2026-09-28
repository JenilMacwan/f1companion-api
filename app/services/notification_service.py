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
        title = "🟡 Safety Car"
        body = msg_text if msg_text else "The Safety Car has been deployed."
    elif flag == "YELLOW" and "DOUBLE" in msg_text.upper():
        title = "🟡 Double Yellow Flags"
        body = msg_text
    elif category == "SessionStatus":
        title = "🏁 Session Update"
        body = msg_text if msg_text else "Track status updated."
    
    # If it's a major event we identified, send the notification
    if title and body:
        send_topic_notification(
            topic=topic,
            title=title,
            body=body,
            data={
                "category": str(category), 
                "flag": str(flag),
                "type": "live_event" # CRITICAL: Routes to the "Race Control" UI label
            }
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
        "url": article.get("link", ""),
        "image_url": article.get("image_url", article.get("image", "")),
        "type": "breaking_news" # CRITICAL: Routes to the "Breaking News" UI label
    }
    
    send_topic_notification(topic, title, body, data)

def notify_standings_update(top_driver: Dict[str, Any]):
    """
    Sends a push notification when championship standings are updated.
    """
    topic = "standings_updates"
    title = "Championship Lead Change!"
    
    driver_name = top_driver.get("name", "Unknown Driver")
    points = top_driver.get("points", "0")
    
    body = f"{driver_name} leads the championship with {points} points."
    
    # CRITICAL: Include the data dict with the standings type
    send_topic_notification(topic, title, body, data={"type": "standings"})

import re

def _clean_team_name(team: str) -> str:
    """Removes sponsors and standardizes team names."""
    lower = team.lower()
    if "mclaren" in lower: return "McLaren"
    if "red bull" in lower: return "Red Bull Racing"
    if "mercedes" in lower: return "Mercedes"
    if "ferrari" in lower: return "Ferrari"
    if "aston martin" in lower: return "Aston Martin"
    if "alpine" in lower: return "Alpine"
    if "williams" in lower: return "Williams"
    if "haas" in lower: return "Haas"
    if "audi" in lower: return "Audi"
    if "cadillac" in lower: return "Cadillac"
    if "rb" in lower or "racing bulls" in lower: return "RB"
    return team

def _clean_driver_name(driver: str) -> str:
    """Removes driver numbers and trailing spaces."""
    return re.sub(r'\s+#?\d+$', '', driver).strip()

def _sanitize_topic(input_str: str) -> str:
    """Sanitizes strings for FCM topics exactly like the Android app."""
    s = input_str.strip().lower()
    s = re.sub(r'[^a-z0-9-_.~%]', '_', s)
    s = re.sub(r'_+', '_', s)
    return s.strip('_')

def _get_driver_topic(driver_name: str) -> str:
    """Generates a valid FCM topic string for a specific driver."""
    clean_name = _clean_driver_name(driver_name)
    return _sanitize_topic(f"favorite_driver_{clean_name}")

def notify_favorite_driver_championship_position_change(driver_name: str, new_position: int):
    """
    Sends a push notification when a favorite driver's position changes.
    """
    topic = _get_driver_topic(driver_name)
    title = f"{driver_name} Update"
    body = f"{driver_name} is now in {new_position}th position in the Championship standings."
    data = {
        "type": "favorite_driver_championship_position_change",
        "driver_name": driver_name,
        "new_position": str(new_position),
    }
    send_topic_notification(topic, title, body, data)

def notify_favorite_driver_fastest_lap(driver_name: str, race_name: str, session_name: str):
    """
    Sends a push notification when a favorite driver sets the fastest lap.
    """
    topic = _get_driver_topic(driver_name)
    title = f"{driver_name} Fastest Lap! ⏱️"
    body = f"{driver_name} has set the fastest lap in the {session_name} at {race_name}."
    data = {
        "type": "favorite_driver_fastest_lap",
        "driver_name": driver_name,
        "race_name": race_name,
        "session_name": session_name
    }
    send_topic_notification(topic, title, body, data)

def notify_favorite_driver_podium(driver_name: str, race_name: str, session_name: str):
    """
    Sends a push notification when a favorite driver reaches the podium.
    """
    topic = _get_driver_topic(driver_name)
    title = f"{driver_name} on the Podium! 🏆"
    body = f"{driver_name} has finished in the top 3 at the {session_name} in {race_name}!"
    data = {
        "type": "favorite_driver_podium",
        "driver_name": driver_name,
        "race_name": race_name,
        "session_name": session_name
    }
    send_topic_notification(topic, title, body, data)

def notify_favorite_driver_retirement(driver_name: str, race_name: str, session_name: str):
    """
    Sends a push notification when a favorite driver retires from the race.
    """
    topic = _get_driver_topic(driver_name)
    title = f"{driver_name} Retired ❌"
    body = f"{driver_name} has retired from the {session_name} at {race_name}."
    data = {
        "type": "favorite_driver_retirement",
        "driver_name": driver_name,
        "race_name": race_name,
        "session_name": session_name
    }
    send_topic_notification(topic, title, body, data)

def notify_favorite_driver_finish(driver_name: str, race_name: str, session_name: str, final_position: int):
    """
    Sends a push notification when a favorite driver finishes the race.
    """
    topic = _get_driver_topic(driver_name)
    title = f"{driver_name} Finished! 🏁"
    body = f"{driver_name} has finished the {session_name} at {race_name} in {final_position}th position."
    data = {
        "type": "favorite_driver_finish",
        "driver_name": driver_name,
        "race_name": race_name,
        "session_name": session_name,
        "final_position": str(final_position)
    }
    send_topic_notification(topic, title, body, data)

def notify_favorite_driver_pole_position(driver_name: str, race_name: str, session_name: str):
    """
    Sends a push notification when a favorite driver takes pole position.
    """
    topic = _get_driver_topic(driver_name)
    title = f"{driver_name} on Pole! 🏎️💨"
    body = f"{driver_name} has secured pole position for the {session_name} at {race_name}!"
    data = {
        "type": "favorite_driver_pole_position",
        "driver_name": driver_name,
        "race_name": race_name,
        "session_name": session_name
    }
    send_topic_notification(topic, title, body, data)

def notify_favorite_driver_qualifying_position(driver_name: str, race_name: str, position: int):
    """
    Sends a push notification showing the final qualifying position for a favorite driver.
    """
    topic = _get_driver_topic(driver_name)
    
    # Optional: Customize message if they got Pole
    if position == 1:
        title = f"{driver_name} takes Pole! 🏎️💨"
        body = f"{driver_name} has secured pole position for the {race_name}!"
    else:
        title = f"{driver_name} Qualifying Result ⏱️"
        body = f"{driver_name} has qualified P{position} for the {race_name}."
        
    data = {
        "type": "favorite_driver_qualifying",
        "driver_name": driver_name,
        "race_name": race_name,
        "position": str(position)
    }
    send_topic_notification(topic, title, body, data)

def _get_team_topic(team_name: str) -> str:
    """Generates a valid FCM topic string for a specific team."""
    clean_team = _clean_team_name(team_name)
    return _sanitize_topic(f"favorite_team_{clean_team}")

def notify_favorite_team_championship_position_change(team_name: str, new_position: int):
    """
    Sends a push notification when a favorite team's position changes.
    """
    topic = _get_team_topic(team_name)
    title = f"{team_name} Update"
    body = f"{team_name} is now in {new_position}th position in the Constructors' Championship."
    data = {
        "type": "favorite_team_championship_position_change",
        "team_name": team_name,
        "new_position": str(new_position),
    }
    send_topic_notification(topic, title, body, data)

def notify_favorite_team_podium(team_name: str, driver_name: str, race_name: str, session_name: str):
    """
    Sends a push notification when a favorite team's driver reaches the podium.
    """
    topic = _get_team_topic(team_name)
    title = f"{team_name} Podium! 🏆"
    body = f"{driver_name} has secured a podium for {team_name} at the {session_name} in {race_name}!"
    data = {
        "type": "favorite_team_podium",
        "team_name": team_name,
        "driver_name": driver_name,
        "race_name": race_name,
        "session_name": session_name
    }
    send_topic_notification(topic, title, body, data)

def notify_favorite_team_win(team_name: str, driver_name: str, race_name: str, session_name: str):
    """
    Sends a push notification when a favorite team wins the race.
    """
    topic = _get_team_topic(team_name)
    title = f"{team_name} Wins! 🥇"
    body = f"{driver_name} has won the {session_name} at {race_name} for {team_name}!"
    data = {
        "type": "favorite_team_win",
        "team_name": team_name,
        "driver_name": driver_name,
        "race_name": race_name,
        "session_name": session_name
    }
    send_topic_notification(topic, title, body, data)

def notify_favorite_team_pole_position(team_name: str, driver_name: str, race_name: str, session_name: str):
    """
    Sends a push notification when a favorite team's driver takes pole position.
    """
    topic = _get_team_topic(team_name)
    title = f"{team_name} on Pole! 🏎️💨"
    body = f"{driver_name} has secured pole position for {team_name} at the {session_name} in {race_name}!"
    data = {
        "type": "favorite_team_pole_position",
        "team_name": team_name,
        "driver_name": driver_name,
        "race_name": race_name,
        "session_name": session_name
    }
    send_topic_notification(topic, title, body, data)