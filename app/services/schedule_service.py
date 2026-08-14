"""
Schedule service.

Responsible for fetching the season schedule, cleaning data,
and formatting the schedule response.
"""

from datetime import datetime, timedelta, timezone
from app.core.config import SCHEDULE_URL
from app.core.http_client import http_client
from app.utils.datetime_utils import parse_race_datetime
from app.utils.flags import get_clean_flag

# Buffer added on top of race start time before a round is considered
# "completed". A race takes ~2 hours to run, and upstream result feeds
# (Jolpica/Ergast) take some additional time to ingest and publish
# results after the chequered flag. Without this buffer, is_completed
# flips to True the moment the race starts — well before results
# exist — causing downstream consumers (points progression, career
# stats) to silently treat "no data yet" as "scored 0 points".
RESULTS_PUBLISH_BUFFER = timedelta(hours=4)


def get_schedule():
    """
    Fetch and clean the full season schedule.

    Returns:
        Dict with season, race count, and cleaned schedule list.

    Raises:
        requests.exceptions.RequestException: On API fetch failure.
    """
    data = http_client.fetch_json(SCHEDULE_URL)
    races_raw = data["MRData"]["RaceTable"]["Races"]

    clean_schedule = []
    for race in races_raw:
        country = race["Circuit"]["Location"]["country"]
        race_datetime = parse_race_datetime(
            race["date"], race.get("time", "00:00:00Z")
        )
        race_entry = {
            "round": race["round"],
            "flag_emoji": get_clean_flag(country),
            "racename": race["raceName"],
            "circuitid": race["Circuit"]["circuitId"],
            "circuitname": race["Circuit"]["circuitName"],
            "circuitlocation": race["Circuit"]["Location"]["locality"],
            "circuitcountry": country,
            "GrandPrix": race["date"],
            "time": race.get("time", "TBA"),
            "is_completed": (
                race_datetime + RESULTS_PUBLISH_BUFFER
            ) < datetime.now(timezone.utc),
            "is_sprint_weekend": "Sprint" in race or "SprintQualifying" in race
        }

        sessions = [
            "FirstPractice",
            "SecondPractice",
            "ThirdPractice",
            "Qualifying",
            "Sprint",
            "SprintQualifying"
        ]

        for session in sessions:
            session_data = race.get(session)
            if session_data:
                race_entry[session] = {
                    "date": session_data.get("date"),
                    "time": session_data.get("time")
                }

        clean_schedule.append(race_entry)

    return {
        "season": data["MRData"]["RaceTable"]["season"],
        "races": len(clean_schedule),
        "schedule": clean_schedule
    }