"""
Constructor service.

Responsible for fetching constructor information and building enriched
constructor profiles that combine identity, logo, drivers, and career statistics.
"""

from datetime import datetime, timezone
from app.core.config import CONSTRUCTORS_URL
from app.core.http_client import http_client
from app.data.constructor_stats import CONSTRUCTOR_BASE_STATS
from app.utils.helpers import stats, get_constructor_logo
from app.utils.helpers import get_constructor_car


def get_constructors():

    data = http_client.fetch_json(CONSTRUCTORS_URL)
    constructors_raw = data["MRData"]["ConstructorTable"]["Constructors"]

    clean_constructors = []
    for constructor in constructors_raw:
        constructor_entry = {
            "constructorid": constructor["constructorId"],
            "name": constructor["name"],
            "nationality": constructor["nationality"],
            "url": constructor["url"]
        }
        clean_constructors.append(constructor_entry)

    return {
        "season": data["MRData"]["ConstructorTable"]["season"],
        "total_constructors": len(clean_constructors),
        "constructors": clean_constructors
    }


def get_constructor_profiles():
    
    from app.services.stats_service import ensure_champs_fetched
    ensure_champs_fetched()

    current_year = str(datetime.now(timezone.utc).year)

    # --- Fetch current constructors list ---
    current_res = http_client.fetch_json(stats("current/constructors.json"))
    current_constructors = current_res["MRData"]["ConstructorTable"]["Constructors"]

    # --- Fetch current standings (for position + points) ---
    current_standings_map = {}
    try:
        cs_res = http_client.fetch_json_safe(
            stats("current/constructorStandings.json")
        )
        if cs_res:
            cs_data = cs_res["MRData"]["StandingsTable"]["StandingsLists"]
            if cs_data:
                for standing in cs_data[0]["ConstructorStandings"]:
                    c_id = standing["Constructor"]["constructorId"]
                    current_standings_map[c_id] = {
                        "position": standing.get("position", "N/A"),
                        "points": standing.get("points", "0")
                    }
    except Exception:
        pass

    # --- Fetch driver standings (to map drivers to constructors) ---
    constructor_drivers = {}
    try:
        ds_res = http_client.fetch_json_safe(
            stats("current/driverStandings.json")
        )
        if ds_res:
            ds_data = ds_res["MRData"]["StandingsTable"]["StandingsLists"]
            if ds_data:
                for d_item in ds_data[0]["DriverStandings"]:
                    driver_info = d_item.get("Driver", {})
                    d_name = f"{driver_info.get('givenName')} {driver_info.get('familyName')}"
                    for c in d_item.get("Constructors", []):
                        c_id = c.get("constructorId")
                        if c_id not in constructor_drivers:
                            constructor_drivers[c_id] = []
                        if d_name not in constructor_drivers[c_id]:
                            constructor_drivers[c_id].append(d_name)
    except Exception:
        pass

    # --- Fetch current year race results ---
    current_year_races = []
    try:
        res = http_client.fetch_json_safe(
            stats(f"{current_year}/results.json?limit=1000")
        )
        if res:
            current_year_races = res["MRData"]["RaceTable"]["Races"]
    except Exception:
        pass

    # --- Compute current year stats per constructor ---
    current_year_stats = {}
    for race in current_year_races:
        participating = set()
        for result in race["Results"]:
            c_id = result["Constructor"]["constructorId"]
            participating.add(c_id)
            if c_id not in current_year_stats:
                current_year_stats[c_id] = {"wins": 0, "podiums": 0, "entries": 0}

            pos = result.get("position")
            if pos == "1":
                current_year_stats[c_id]["wins"] += 1
            if pos in ["1", "2", "3"]:
                current_year_stats[c_id]["podiums"] += 1

        for c_id in participating:
            current_year_stats[c_id]["entries"] += 1

    # --- Build enriched profiles ---
    profiles = []
    for constructor in current_constructors:
        c_id = constructor["constructorId"]

        # Identity
        name = constructor.get("name", "Unknown")
        nationality = constructor.get("nationality", "Unknown")

        # Logo
        logo_url = get_constructor_logo(c_id)

        # Car
        car_image_url = get_constructor_car(c_id) 

        # Drivers
        drivers = constructor_drivers.get(c_id, [])

        # Career stats (baseline + current year)
        base = CONSTRUCTOR_BASE_STATS.get(
            c_id, {"wcc": 0, "wdc": 0, "wins": 0, "entries": 0, "podiums": 0}
        )
        cy = current_year_stats.get(
            c_id, {"wins": 0, "podiums": 0, "entries": 0}
        )

        total_wins = base["wins"] + cy["wins"]
        total_podiums = base["podiums"] + cy["podiums"]
        total_entries = base["entries"] + cy["entries"]

        win_rate = round((total_wins / total_entries * 100), 2) if total_entries > 0 else 0
        podium_rate = round((total_podiums / (total_entries * 2) * 100), 2) if total_entries > 0 else 0

        # Current season standing
        standing_info = current_standings_map.get(c_id, {})
        current_season = {
            "year": current_year,
            "position": standing_info.get("position", "N/A"),
            "points": standing_info.get("points", "0")
        }

        profiles.append({
            "constructor_id": c_id,
            "name": name,
            "nationality": nationality,
            "logo": logo_url,
            "car": car_image_url,   
            "drivers": drivers if drivers else "N/A",
            "career_stats": {
                "constructor_championships": base["wcc"],
                "driver_championships": base["wdc"],
                "total_races": total_entries,
                "wins": total_wins,
                "win_percentage": f"{win_rate}%",
                "podiums": total_podiums,
                "podium_percentage": f"{podium_rate}%",
                "current_season": current_season
            }
        })

    return {
        "season": current_year,
        "total_constructors": len(profiles),
        "constructors": profiles
    }
