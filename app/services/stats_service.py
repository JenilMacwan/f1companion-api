"""
Stats service.

Responsible for driver career statistics, constructor statistics,
championship calculations, and dynamic yearly updates.
"""

from datetime import datetime, timezone
from app.core.http_client import http_client
from app.core.logging import logger
from app.data.championships import (
    GLOBAL_WDC_MAP, GLOBAL_WCC_MAP, GLOBAL_DRIVER_WCC_MAP, UPDATED_YEARS
)
from app.data.driver_stats import DRIVER_BASE_STATS
from app.data.constructor_stats import CONSTRUCTOR_BASE_STATS


def update_dynamic_championships():
    """
    Update championship maps for years between 2025 and the current year.

    This avoids rate-limiting the API with 150+ historical queries by only
    fetching results for years not yet in the static baseline.
    Mutates GLOBAL_WDC_MAP, GLOBAL_WCC_MAP, GLOBAL_DRIVER_WCC_MAP in place.
    """
    current_year = datetime.now(timezone.utc).year
    for year in range(2025, current_year):
        if year in UPDATED_YEARS:
            continue
        try:
            r1 = http_client.fetch_json_safe(
                f"https://api.jolpi.ca/ergast/f1/{year}/driverStandings.json"
            )
            if r1:
                st1 = r1["MRData"]["StandingsTable"]["StandingsLists"]
                if st1:
                    d_id = st1[0]["DriverStandings"][0]["Driver"]["driverId"]
                    c_id = st1[0]["DriverStandings"][0]["Constructors"][0]["constructorId"]
                    GLOBAL_WDC_MAP[d_id] = GLOBAL_WDC_MAP.get(d_id, 0) + 1
                    GLOBAL_DRIVER_WCC_MAP[c_id] = GLOBAL_DRIVER_WCC_MAP.get(c_id, 0) + 1

            r2 = http_client.fetch_json_safe(
                f"https://api.jolpi.ca/ergast/f1/{year}/constructorStandings.json"
            )
            if r2:
                st2 = r2["MRData"]["StandingsTable"]["StandingsLists"]
                if st2:
                    c_id2 = st2[0]["ConstructorStandings"][0]["Constructor"]["constructorId"]
                    GLOBAL_WCC_MAP[c_id2] = GLOBAL_WCC_MAP.get(c_id2, 0) + 1

            UPDATED_YEARS.add(year)
        except Exception:
            pass


def ensure_champs_fetched():
    """Ensure dynamic championship data has been fetched for recent years."""
    update_dynamic_championships()


def get_constructor_stats():
    """
    Compute deep career stats for all constructors on the current grid.

    Combines hardcoded baseline stats with dynamically fetched current-year data.

    Returns:
        Dict with season, total constructors, and stats list.

    Raises:
        Exception: On API or processing failure.
    """
    ensure_champs_fetched()
    current_year = str(datetime.now(timezone.utc).year)

    current_res = http_client.fetch_json(
        "https://api.jolpi.ca/ergast/f1/current/constructors.json"
    )
    current_constructors = current_res["MRData"]["ConstructorTable"]["Constructors"]

    # Fetch current standings
    current_standings_map = {}
    try:
        cs_res = http_client.fetch_json_safe(
            "https://api.jolpi.ca/ergast/f1/current/constructorStandings.json"
        )
        if cs_res:
            cs_data = cs_res["MRData"]["StandingsTable"]["StandingsLists"]
            if cs_data:
                for standing in cs_data[0]["ConstructorStandings"]:
                    c_id = standing["Constructor"]["constructorId"]
                    current_standings_map[c_id] = {
                        "year": current_year,
                        "position": standing.get("position", "N/A"),
                        "points": standing.get("points", "0")
                    }
    except Exception:
        pass

    # Fetch current year race results
    current_year_races = []
    try:
        res = http_client.fetch_json_safe(
            f"https://api.jolpi.ca/ergast/f1/{current_year}/results.json?limit=1000"
        )
        if res:
            current_year_races = res["MRData"]["RaceTable"]["Races"]
    except Exception:
        pass

    # Compute current year stats
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

    # Build response
    grid_stats = []
    for constructor in current_constructors:
        c_id = constructor["constructorId"]

        base = CONSTRUCTOR_BASE_STATS.get(
            c_id, {"wcc": 0, "wdc": 0, "wins": 0, "entries": 0, "podiums": 0}
        )
        cy_stats = current_year_stats.get(
            c_id, {"wins": 0, "podiums": 0, "entries": 0}
        )

        total_wins = base["wins"] + cy_stats["wins"]
        total_podiums = base["podiums"] + cy_stats["podiums"]
        total_entries = base["entries"] + cy_stats["entries"]

        win_rate = round((total_wins / total_entries * 100), 2) if total_entries > 0 else 0
        podium_rate = round((total_podiums / (total_entries * 2) * 100), 2) if total_entries > 0 else 0

        c_stats = current_standings_map.get(
            c_id, {"year": current_year, "position": "N/A", "points": "0"}
        )

        grid_stats.append({
            "constructor_id": c_id,
            "constructor_name": constructor["name"],
            "stats": {
                "constructor_championships": base["wcc"],
                "driver_championships": base["wdc"],
                "total_races": total_entries,
                "wins": total_wins,
                "win_percentage": f"{win_rate}%",
                "podiums": total_podiums,
                "podium_percentage": f"{podium_rate}%",
                "current_season": c_stats
            }
        })

    return {
        "season": current_year,
        "total_constructors": len(grid_stats),
        "constructor_stats": grid_stats
    }


def get_driver_stats():
    """
    Compute deep career stats for all drivers on the current grid.

    Combines hardcoded baseline stats with dynamically fetched current-year data.

    Returns:
        Dict with season, total drivers, and stats list.

    Raises:
        Exception: On API or processing failure.
    """
    ensure_champs_fetched()
    current_year = str(datetime.now(timezone.utc).year)

    current_res = http_client.fetch_json(
        "https://api.jolpi.ca/ergast/f1/current/drivers.json"
    )
    current_drivers = current_res["MRData"]["DriverTable"]["Drivers"]

    # Fetch current standings
    current_standings_map = {}
    try:
        cs_res = http_client.fetch_json_safe(
            "https://api.jolpi.ca/ergast/f1/current/driverStandings.json"
        )
        if cs_res:
            cs_data = cs_res["MRData"]["StandingsTable"]["StandingsLists"]
            if cs_data:
                for standing in cs_data[0]["DriverStandings"]:
                    d_id = standing["Driver"]["driverId"]
                    current_standings_map[d_id] = {
                        "year": current_year,
                        "position": standing.get("position", "N/A"),
                        "points": standing.get("points", "0")
                    }
    except Exception:
        pass

    # Fetch current year race results
    current_year_races = []
    try:
        res = http_client.fetch_json_safe(
            f"https://api.jolpi.ca/ergast/f1/{current_year}/results.json?limit=1000"
        )
        if res:
            current_year_races = res["MRData"]["RaceTable"]["Races"]
    except Exception:
        pass

    # Compute current year stats per driver
    current_year_stats = {}
    for race in current_year_races:
        for result in race["Results"]:
            d_id = result["Driver"]["driverId"]
            if d_id not in current_year_stats:
                current_year_stats[d_id] = {
                    "races": 0, "wins": 0, "podiums": 0, "pole": 0, "points": 0.0
                }

            current_year_stats[d_id]["races"] += 1
            current_year_stats[d_id]["points"] += float(result.get("points", 0.0))

            pos = result.get("position")
            if pos == "1":
                current_year_stats[d_id]["wins"] += 1
            if pos in ["1", "2", "3"]:
                current_year_stats[d_id]["podiums"] += 1
            if result.get("grid") == "1":
                current_year_stats[d_id]["pole"] += 1

    # Build response
    grid_stats = []
    for driver in current_drivers:
        d_id = driver["driverId"]
        base = DRIVER_BASE_STATS.get(d_id, {
            "total_races": 0, "total_pole": 0, "total_wins": 0,
            "total_podiums": 0, "career_points": 0.0, "total_seasons": 0
        })
        cy_stats = current_year_stats.get(d_id, {
            "races": 0, "wins": 0, "podiums": 0, "pole": 0, "points": 0.0
        })

        seasons_played = base["total_seasons"] + 1
        wdc_count = GLOBAL_WDC_MAP.get(d_id, 0)
        c_stats = current_standings_map.get(
            d_id, {"year": current_year, "position": "N/A", "points": "0"}
        )

        grid_stats.append({
            "driver_id": d_id,
            "driver_name": f"{driver['givenName']} {driver['familyName']}",
            "career_stats": {
                "world_championships": wdc_count,
                "total_races": base["total_races"] + cy_stats["races"],
                "total_pole": base["total_pole"] + cy_stats["pole"],
                "total_wins": base["total_wins"] + cy_stats["wins"],
                "total_podiums": base["total_podiums"] + cy_stats["podiums"],
                "career_points": round(base["career_points"] + cy_stats["points"], 1),
                "total_seasons": seasons_played,
                "current_season": c_stats
            },
        })

    return {
        "season": current_year,
        "total_drivers": len(grid_stats),
        "driver_stats": grid_stats
    }
