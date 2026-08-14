"""
Constructor service.

Responsible for fetching constructor information and building enriched
constructor profiles that combine identity, logo, drivers, and career statistics.
"""

from datetime import datetime, timezone
from app.core.config import CONSTRUCTORS_URL
from app.core.http_client import http_client
from app.data.constructor_stats import CONSTRUCTOR_BASE_STATS
from app.services.schedule_service import get_schedule
from app.services.round_results_service import get_round_results
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


def _parse_constructor_round(current_year, rnd):
    """
    Parse per-constructor race + sprint points/positions for one round
    from the shared, cached round-results fetch (see round_results_service).
    A constructor can have two drivers scoring in the same race, so
    points and positions are aggregated per constructor.

    Returns:
        Tuple of (race_points, race_positions, sprint_points, race_data_available):
        - race_points: {constructor_id: points_scored_in_race}
        - race_positions: {constructor_id: [finishing_positions]}
        - sprint_points: {constructor_id: points_scored_in_sprint}
        - race_data_available: True only if results are published for this round
    """
    round_data = get_round_results(current_year, rnd)

    race_points = {}
    race_positions = {}
    for result in round_data["race_results"]:
        c_id = result["Constructor"]["constructorId"]
        pts = float(result.get("points", 0.0))
        race_points[c_id] = race_points.get(c_id, 0.0) + pts
        race_positions.setdefault(c_id, []).append(result.get("position"))

    sprint_points = {}
    for result in round_data["sprint_results"]:
        c_id = result["Constructor"]["constructorId"]
        pts = float(result.get("points", 0.0))
        sprint_points[c_id] = sprint_points.get(c_id, 0.0) + pts

    return race_points, race_positions, sprint_points, round_data["race_data_available"]


def get_constructor_profiles():
    """
    Build enriched profiles for all constructors on the current grid.

    Points progression is built from the shared, cached per-round
    results (round_results_service), and includes both the points
    scored that round and the running cumulative total for the
    season. Rounds still pending results upstream are skipped
    entirely rather than shown as a false 0.
    """
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

    # --- Fetch schedule to determine completed rounds ---
    schedule_data = get_schedule()
    completed_rounds = [r for r in schedule_data["schedule"] if r.get("is_completed")]

    # --- Parse per-round race + sprint results (shared cache) ---
    race_points_map_c = {}     # {round: {constructor_id: points}}
    race_positions_map_c = {}  # {round: {constructor_id: [positions]}}
    sprint_points_map_c = {}   # {round: {constructor_id: points}}
    rounds_with_data = []      # completed rounds that actually have published results

    for r_entry in completed_rounds:
        rnd = str(r_entry["round"])
        race_points, race_positions, sprint_points, race_data_available = _parse_constructor_round(
            current_year, rnd
        )
        race_points_map_c[rnd] = race_points
        race_positions_map_c[rnd] = race_positions
        sprint_points_map_c[rnd] = sprint_points
        if race_data_available:
            rounds_with_data.append(r_entry)

    # --- Compute current year stats per constructor from per-round data ---
    # Only rounds with published results are counted — a round pending
    # results upstream must not silently count as 0 points scored.
    current_year_stats = {}
    for r_entry in rounds_with_data:
        rnd = str(r_entry["round"])
        for c_id in race_points_map_c.get(rnd, {}).keys():
            if c_id not in current_year_stats:
                current_year_stats[c_id] = {"wins": 0, "podiums": 0, "entries": 0}

            current_year_stats[c_id]["entries"] += 1
            positions = race_positions_map_c.get(rnd, {}).get(c_id, [])
            if "1" in positions:
                current_year_stats[c_id]["wins"] += 1
            if any(p in ["1", "2", "3"] for p in positions):
                current_year_stats[c_id]["podiums"] += 1

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
            "points": standing_info.get("points", "0"),
            "points_progression": []
        }

        # Construct complete points progression using schedule,
        # tracking both the points scored per round and the
        # cumulative running total for the season — matching the
        # driver profile pattern of including every completed round.
        cumulative_points = 0.0
        for r_entry in completed_rounds:
            rnd = str(r_entry["round"])
            r_name = r_entry["racename"]
            r_pts = race_points_map_c.get(rnd, {}).get(c_id, 0.0)
            s_pts = sprint_points_map_c.get(rnd, {}).get(c_id, 0.0)
            round_points = r_pts + s_pts
            cumulative_points += round_points

            current_season["points_progression"].append({
                "round": rnd,
                "race_name": r_name,
                "points": round_points,
                "cumulative_points": round(cumulative_points, 1)
            })

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