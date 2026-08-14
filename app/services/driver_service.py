"""
Driver service.

Responsible for fetching driver information and building enriched driver profiles
that combine identity, team, image, and career statistics.
"""

from datetime import datetime, timezone
from app.core.config import DRIVERS_URL
from app.core.constants import OFFICIAL_DRIVERS_2026
from app.core.http_client import http_client
from app.data.championships import GLOBAL_WDC_MAP
from app.data.driver_stats import DRIVER_BASE_STATS
from app.services.schedule_service import get_schedule
from app.services.round_results_service import get_round_results
from app.utils.helpers import stats, get_driver_image


def get_drivers():
    """
    Fetch and clean the current season's driver lineup (lightweight).

    Returns:
        Dict with season, total driver count, and cleaned drivers list.

    Raises:
        requests.exceptions.RequestException: On API fetch failure.
    """
    data = http_client.fetch_json(DRIVERS_URL)
    drivers_raw = data["MRData"]["DriverTable"]["Drivers"]

    clean_drivers = []
    for driver in drivers_raw:
        if driver.get("driverId") not in OFFICIAL_DRIVERS_2026:
            continue
        driver_entry = {
            "driverid": driver.get("driverId", "Unknown"),
            "firstname": driver.get("givenName", "Unknown"),
            "lastname": driver.get("familyName", "Unknown"),
            "nationality": driver.get("nationality", "Unknown"),
        }

        if "permanentNumber" in driver and driver["permanentNumber"]:
            driver_entry["number"] = driver["permanentNumber"]
        else:
            driver_entry["number"] = "TBA"

        if "code" in driver and driver["code"]:
            driver_entry["code"] = driver["code"]
        else:
            driver_entry["code"] = "---"

        clean_drivers.append(driver_entry)

    return {
        "season": data["MRData"]["DriverTable"]["season"],
        "total_drivers": len(clean_drivers),
        "drivers": clean_drivers
    }


def _parse_driver_round(current_year, rnd):
    """
    Parse per-driver race + sprint points/meta for one round from the
    shared, cached round-results fetch (see round_results_service).

    Returns:
        Tuple of (race_points, race_meta, sprint_points, race_data_available):
        - race_points: {driver_id: points_scored_in_race}
        - race_meta: {driver_id: {"position": ..., "grid": ...}}
        - sprint_points: {driver_id: points_scored_in_sprint}
        - race_data_available: True only if results are published for this round
    """
    round_data = get_round_results(current_year, rnd)

    race_points = {}
    race_meta = {}
    for result in round_data["race_results"]:
        d_id = result["Driver"]["driverId"]
        race_points[d_id] = float(result.get("points", 0.0))
        race_meta[d_id] = {
            "position": result.get("position"),
            "grid": result.get("grid")
        }

    sprint_points = {}
    for result in round_data["sprint_results"]:
        d_id = result["Driver"]["driverId"]
        sprint_points[d_id] = float(result.get("points", 0.0))

    return race_points, race_meta, sprint_points, round_data["race_data_available"]


def get_driver_profiles():
    """
    Build enriched profiles for all drivers on the current grid.

    Combines driver identity (name, number, code, nationality),
    driver image, current team, and full career statistics
    (baseline + current year dynamic data).

    Points progression is built from the shared, cached per-round
    results (round_results_service), and includes both the points
    scored that round and the running cumulative total for the
    season. Rounds still pending results upstream are skipped
    entirely rather than shown as a false 0.

    Returns:
        Dict with season, total drivers, and enriched profiles list.

    Raises:
        Exception: On API or processing failure.
    """
    from app.services.stats_service import ensure_champs_fetched
    ensure_champs_fetched()

    current_year = str(datetime.now(timezone.utc).year)

    # --- Fetch current drivers list ---
    current_res = http_client.fetch_json(stats("current/drivers.json"))
    current_drivers = current_res["MRData"]["DriverTable"]["Drivers"]

    # --- Fetch current standings (for team + position + points) ---
    current_standings_map = {}
    try:
        cs_res = http_client.fetch_json_safe(
            stats("current/driverStandings.json")
        )
        if cs_res:
            cs_data = cs_res["MRData"]["StandingsTable"]["StandingsLists"]
            if cs_data:
                for standing in cs_data[0]["DriverStandings"]:
                    d_id = standing["Driver"]["driverId"]
                    constructors = standing.get("Constructors", [])
                    team_name = constructors[0].get("name", "N/A") if constructors else "N/A"
                    current_standings_map[d_id] = {
                        "team": team_name,
                        "position": standing.get("position", "N/A"),
                        "points": standing.get("points", "0")
                    }
    except Exception:
        pass

    # --- Fetch schedule to determine completed rounds ---
    schedule_data = get_schedule()
    completed_rounds = [r for r in schedule_data["schedule"] if r.get("is_completed")]

    # --- Parse per-round race + sprint results (shared cache) ---
    race_points_map = {}      # {round: {driver_id: points}}
    race_meta_map = {}        # {round: {driver_id: {"position":..., "grid":...}}}
    sprint_points_map = {}    # {round: {driver_id: points}}
    rounds_with_data = []     # completed rounds that actually have published results

    for r_entry in completed_rounds:
        rnd = str(r_entry["round"])
        race_points, race_meta, sprint_points, race_data_available = _parse_driver_round(
            current_year, rnd
        )
        race_points_map[rnd] = race_points
        race_meta_map[rnd] = race_meta
        sprint_points_map[rnd] = sprint_points
        if race_data_available:
            rounds_with_data.append(r_entry)

    # --- Compute current year stats per driver from per-round data ---
    # Only rounds with published results are counted — a round pending
    # results upstream must not silently count as 0 points scored.
    current_year_stats = {}
    for r_entry in rounds_with_data:
        rnd = str(r_entry["round"])
        for d_id, race_pts in race_points_map.get(rnd, {}).items():
            if d_id not in current_year_stats:
                current_year_stats[d_id] = {
                    "races": 0, "wins": 0, "podiums": 0, "pole": 0, "points": 0.0
                }
            meta = race_meta_map.get(rnd, {}).get(d_id, {})
            sprint_pts = sprint_points_map.get(rnd, {}).get(d_id, 0.0)

            current_year_stats[d_id]["races"] += 1
            current_year_stats[d_id]["points"] += race_pts + sprint_pts

            if meta.get("position") == "1":
                current_year_stats[d_id]["wins"] += 1
            if meta.get("position") in ["1", "2", "3"]:
                current_year_stats[d_id]["podiums"] += 1
            if meta.get("grid") == "1":
                current_year_stats[d_id]["pole"] += 1

    # --- Build enriched profiles ---
    profiles = []
    for driver in current_drivers:
        d_id = driver["driverId"]

        if d_id not in OFFICIAL_DRIVERS_2026:
            continue

        # Identity
        first_name = driver.get("givenName", "Unknown")
        last_name = driver.get("familyName", "Unknown")
        number = driver.get("permanentNumber", "TBA") or "TBA"
        code = driver.get("code", "---") or "---"
        nationality = driver.get("nationality", "Unknown")

        # Image
        image_url = get_driver_image(d_id)

        # Team from standings
        standing_info = current_standings_map.get(d_id, {})
        team = standing_info.get("team", "N/A")

        # Career stats (baseline + current year)
        base = DRIVER_BASE_STATS.get(d_id, {
            "total_races": 0, "total_pole": 0, "total_wins": 0,
            "total_podiums": 0, "career_points": 0.0, "total_seasons": 0
        })
        cy = current_year_stats.get(d_id, {
            "races": 0, "wins": 0, "podiums": 0, "pole": 0, "points": 0.0
        })

        total_races = base["total_races"] + cy["races"]
        total_wins = base["total_wins"] + cy["wins"]
        total_podiums = base["total_podiums"] + cy["podiums"]
        total_poles = base["total_pole"] + cy["pole"]
        career_points = round(base["career_points"] + cy["points"], 1)
        total_seasons = base["total_seasons"] + 1
        wdc_count = GLOBAL_WDC_MAP.get(d_id, 0)

        current_season = {
            "year": current_year,
            "position": standing_info.get("position", "N/A"),
            "points": standing_info.get("points", "0"),
            "wins": cy["wins"],
            "podiums": cy["podiums"],
            "points_progression": []
        }

        # Construct complete points progression using schedule,
        # tracking both the points scored per round and the
        # cumulative running total for the season. Rounds pending
        # results upstream are skipped entirely rather than shown
        # as a false 0 — they'll appear once results are published.
        cumulative_points = 0.0
        for r_entry in rounds_with_data:
            rnd = str(r_entry["round"])
            r_name = r_entry["racename"]
            r_pts = race_points_map.get(rnd, {}).get(d_id, 0.0)
            s_pts = sprint_points_map.get(rnd, {}).get(d_id, 0.0)
            round_points = r_pts + s_pts
            cumulative_points += round_points

            current_season["points_progression"].append({
                "round": rnd,
                "race_name": r_name,
                "points": round_points,
                "cumulative_points": round(cumulative_points, 1)
            })

        profiles.append({
            "driver_id": d_id,
            "first_name": first_name,
            "last_name": last_name,
            "full_name": f"{first_name} {last_name}",
            "number": number,
            "code": code,
            "nationality": nationality,
            "image": image_url,
            "team": team,
            "career_stats": {
                "world_championships": wdc_count,
                "total_races": total_races,
                "total_poles": total_poles,
                "total_wins": total_wins,
                "total_podiums": total_podiums,
                "career_points": career_points,
                "total_seasons": total_seasons,
                "current_season": current_season
            }
        })

    return {
        "season": current_year,
        "total_drivers": len(profiles),
        "drivers": profiles
    }