"""
Race service.

Responsible for determining the next race, session ordering,
countdown calculations, sprint weekend detection, and race results.
"""

from datetime import datetime, timezone
from app.core.config import SCHEDULE_URL
from app.core.constants import SESSION_KEYS, SESSION_DURATIONS
from app.core.http_client import http_client
from app.services.weather_service import get_track_weather
from app.utils.flags import get_clean_flag
from app.utils.datetime_utils import parse_race_datetime
from app.utils.helpers import get_driver_image


def get_next_race():

    data = http_client.fetch_json(SCHEDULE_URL)
    now = datetime.now(timezone.utc)
    races = data["MRData"]["RaceTable"]["Races"]

    next_event = None
    for race in races:
        race_dt = parse_race_datetime(race["date"], race.get("time", "00:00:00Z"))
        if race_dt > now:
            next_event = race
            break

    if not next_event:
        return {"message": "Season concluded."}

    # Recalculate race_dt for the found next_event
    race_dt = parse_race_datetime(
        next_event["date"], next_event.get("time", "00:00:00Z")
    )

    # Build sessions list
    sessions_list = [{"name": "Race", "dt": race_dt}]
    for key, name in SESSION_KEYS.items():
        session = next_event.get(key)
        if session:
            s_dt = parse_race_datetime(session["date"], session["time"])
            sessions_list.append({"name": name, "dt": s_dt})

    # Sort sessions chronologically
    sessions_list.sort(key=lambda x: x["dt"])

    # Find the target session (next upcoming session)
    target_session_dt = race_dt
    session_name = "Race"
    ongoing_session_name = None

    for i, s in enumerate(sessions_list):
        if s["dt"] > now:
            target_session_dt = s["dt"]
            session_name = s["name"]

            if i > 0:
                prev_s = sessions_list[i - 1]
                duration = SESSION_DURATIONS.get(prev_s["name"], 60)
                if (now - prev_s["dt"]).total_seconds() < (duration * 60):
                    ongoing_session_name = prev_s["name"]
            break

    # Fetch weather
    lat = next_event["Circuit"]["Location"]["lat"]
    lon = next_event["Circuit"]["Location"]["long"]
    weather_info = get_track_weather(lat, lon)

    # Countdown calculation
    delta = target_session_dt - now
    countdown = {
        "days": delta.days,
        "hours": delta.seconds // 3600,
        "minutes": (delta.seconds // 60) % 60,
        "seconds": delta.seconds % 60
    }

    # Next session string
    if ongoing_session_name:
        next_session_str = (
            f"Ongoing : {ongoing_session_name} | Next : {session_name}  "
            f"Time Zone : UTC {target_session_dt.strftime('%Y-%m-%d %H:%M UTC')}"
        )
    else:
        next_session_str = (
            f"Session Name : {session_name}  "
            f"Time Zone : UTC {target_session_dt.strftime('%Y-%m-%d %H:%M UTC')}"
        )

    # Country flag
    country = next_event["Circuit"]["Location"]["country"]

    return {
        "round": race["round"],
        "race_name": next_event["raceName"],
        "circuit": next_event["Circuit"]["circuitName"],
        "country": country,
        "flag_emoji": get_clean_flag(country),
        "weather": weather_info,
        "countdown": countdown,
        "next_session": next_session_str,
        "ongoing_session": ongoing_session_name,
        "is_sprint_weekend": "Sprint" in next_event or "SprintQualifying" in next_event
    }


def get_race_results(round_num, year):
    """
    Fetch results for a specific race by round and year.

    Args:
        round_num: The round number (e.g., "1").
        year: The season year (e.g., "2025").

    Returns:
        Dict with season, round, race name, and results list.

    Raises:
        requests.exceptions.RequestException: On API fetch failure.
    """
    results_url = f"https://api.jolpi.ca/ergast/f1/{year}/{round_num}/results.json"
    data = http_client.fetch_json(results_url)

    races_raw = data["MRData"]["RaceTable"]["Races"]

    if not races_raw:
        return {
            "season": data["MRData"]["RaceTable"]["season"],
            "status": "RESULT NOT YET AVAILABLE",
            "round": round_num,
        }

    race = races_raw[0]
    results_list = race.get("Results", [])

    clean_results = []
    for result in results_list:
        clean_results.append({
            "position": result["position"],
            "positionText": result["positionText"],
            "driver": f"{result['Driver']['givenName']} {result['Driver']['familyName']}",
            "driver_image": get_driver_image(result["Driver"]["driverId"]),
            "constructor": result["Constructor"]["name"],
            "points": result["points"],
            "grid": result["grid"],
            "status": result["status"],
            "time": result["Time"]["time"] if "Time" in result else "N/A",
            "fastest_lap_time": result.get("FastestLap", {}).get("Time", {}).get("time", "N/A")
        })

    return {
        "season": data["MRData"]["RaceTable"]["season"],
        "round": race["round"],
        "race_name": race["raceName"],
        "results": clean_results
    }


def get_qualifying_results(round_num, year):
    """
    Fetch qualifying results for a specific race by round and year.
    """
    results_url = f"https://api.jolpi.ca/ergast/f1/{year}/{round_num}/qualifying.json"
    data = http_client.fetch_json(results_url)

    races_raw = data["MRData"]["RaceTable"]["Races"]

    if not races_raw:
        return {
            "season": data["MRData"]["RaceTable"]["season"],
            "status": "QUALIFYING RESULT NOT YET AVAILABLE",
            "round": round_num,
        }

    race = races_raw[0]
    results_list = race.get("QualifyingResults", [])

    clean_results = []
    for result in results_list:
        clean_results.append({
            "position": result["position"],
            "driver": f"{result['Driver']['givenName']} {result['Driver']['familyName']}",
            "driver_image": get_driver_image(result["Driver"]["driverId"]),
            "constructor": result["Constructor"]["name"],
            "q1": result.get("Q1", "N/A"),
            "q2": result.get("Q2", "N/A"),
            "q3": result.get("Q3", "N/A")
        })

    return {
        "season": data["MRData"]["RaceTable"]["season"],
        "round": race["round"],
        "race_name": race["raceName"],
        "results": clean_results
    }


def get_sprint_results(round_num, year):
    """
    Fetch sprint results for a specific race by round and year.
    """
    results_url = f"https://api.jolpi.ca/ergast/f1/{year}/{round_num}/sprint.json"
    data = http_client.fetch_json(results_url)

    races_raw = data["MRData"]["RaceTable"]["Races"]

    if not races_raw:
        return {
            "season": data["MRData"]["RaceTable"]["season"],
            "status": "SPRINT RESULT NOT YET AVAILABLE",
            "round": round_num,
        }

    race = races_raw[0]
    results_list = race.get("SprintResults", [])

    clean_results = []
    for result in results_list:
        clean_results.append({
            "position": result["position"],
            "positionText": result["positionText"],
            "driver": f"{result['Driver']['givenName']} {result['Driver']['familyName']}",
            "driver_image": get_driver_image(result["Driver"]["driverId"]),
            "constructor": result["Constructor"]["name"],
            "points": result.get("points", "0"),
            "grid": result.get("grid", "N/A"),
            "status": result["status"],
            "time": result.get("Time", {}).get("time", "N/A"),
            "fastest_lap_time": result.get("FastestLap", {}).get("Time", {}).get("time", "N/A")
        })

    return {
        "season": data["MRData"]["RaceTable"]["season"],
        "round": race["round"],
        "race_name": race["raceName"],
        "results": clean_results
    }


def get_sprint_qualifying_results(round_num, year):
    """
    Derive sprint qualifying results by using the sprint grid from a specific race.
    """
    results_url = f"https://api.jolpi.ca/ergast/f1/{year}/{round_num}/sprint.json"
    data = http_client.fetch_json(results_url)

    races_raw = data["MRData"]["RaceTable"]["Races"]

    if not races_raw:
        return {
            "season": data["MRData"]["RaceTable"]["season"],
            "status": "SPRINT QUALIFYING RESULT NOT YET AVAILABLE",
            "round": round_num,
        }

    race = races_raw[0]
    results_list = race.get("SprintResults", [])
    
    # Filter and sort by grid position to reconstruct sprint qualifying
    valid_results = [r for r in results_list if r.get("grid") and r["grid"] != "0"]
    valid_results.sort(key=lambda x: int(x["grid"]))

    clean_results = []
    for result in valid_results:
        clean_results.append({
            "position": result["grid"],
            "driver": f"{result['Driver']['givenName']} {result['Driver']['familyName']}",
            "driver_image": get_driver_image(result["Driver"]["driverId"]),
            "constructor": result["Constructor"]["name"]
        })

    return {
        "season": data["MRData"]["RaceTable"]["season"],
        "round": race["round"],
        "race_name": race["raceName"],
        "results": clean_results
    }
