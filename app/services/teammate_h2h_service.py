"""
Teammate head-to-head service.

Compares drivers within the same constructor across qualifying,
sprint qualifying, sprint race, main race, and championship standings
for the current season.
"""

from datetime import datetime, timezone
from app.core.http_client import http_client
from app.core.logging import logger
from app.core.constants import OFFICIAL_DRIVERS_2026
from app.services.schedule_service import get_schedule
from app.services.round_results_service import get_round_results
from app.utils.helpers import stats, get_driver_image, get_constructor_logo


def _build_driver_constructor_map():
    """
    Fetch current driver standings and build:
      - constructor_drivers: {constructor_id: [{driver info}, ...]}
      - driver_standings: {driver_id: {position, points}}
      - constructor_names: {constructor_id: name}

    Only includes official 2026 drivers.
    """
    constructor_drivers = {}
    driver_standings = {}
    constructor_names = {}

    try:
        ds_res = http_client.fetch_json(
            stats("current/driverStandings.json")
        )
        ds_data = ds_res["MRData"]["StandingsTable"]["StandingsLists"]
        if ds_data:
            for standing in ds_data[0]["DriverStandings"]:
                driver = standing["Driver"]
                d_id = driver["driverId"]

                if d_id not in OFFICIAL_DRIVERS_2026:
                    continue

                driver_standings[d_id] = {
                    "position": standing.get("position", "N/A"),
                    "points": standing.get("points", "0"),
                }

                d_info = {
                    "driver_id": d_id,
                    "name": f"{driver.get('givenName', '')} {driver.get('familyName', '')}",
                    "code": driver.get("code", "---") or "---",
                    "image": get_driver_image(d_id),
                }

                for c in standing.get("Constructors", []):
                    c_id = c.get("constructorId")
                    c_name = c.get("name", "Unknown")
                    constructor_names[c_id] = c_name
                    constructor_drivers.setdefault(c_id, []).append(d_info)
    except Exception as e:
        logger.warning(f"Failed to fetch driver standings for H2H: {e}")

    return constructor_drivers, driver_standings, constructor_names


def _compare_session(driver_a_id, driver_b_id, position_map):
    """
    Compare two drivers' positions in a single session.

    Args:
        driver_a_id: First driver's ID.
        driver_b_id: Second driver's ID.
        position_map: {driver_id: position_str} for this round+session.

    Returns:
        Tuple (driver_a_pos, driver_b_pos, winner) or None if comparison
        is not possible (one or both absent / both DNF).
    """
    a_pos = position_map.get(driver_a_id)
    b_pos = position_map.get(driver_b_id)

    # Both absent — skip
    if a_pos is None and b_pos is None:
        return None

    # One absent — the other wins
    if a_pos is None:
        return "DNS", b_pos, "driver_b"
    if b_pos is None:
        return a_pos, "DNS", "driver_a"

    # Try numeric comparison; non-numeric (e.g. "R" for retired) treated as DNF
    try:
        a_num = int(a_pos)
    except (ValueError, TypeError):
        a_num = None

    try:
        b_num = int(b_pos)
    except (ValueError, TypeError):
        b_num = None

    # Both DNF — skip
    if a_num is None and b_num is None:
        return None

    # One DNF, the other finished
    if a_num is None:
        winner = "driver_b"
    elif b_num is None:
        winner = "driver_a"
    elif a_num < b_num:
        winner = "driver_a"
    elif b_num < a_num:
        winner = "driver_b"
    else:
        winner = "tie"

    return a_pos, b_pos, winner


def _best_quali_position(quali_result):
    """
    Extract the best qualifying time/position from a QualifyingResults entry.
    Returns the qualifying position (which already reflects the best session).
    """
    return quali_result.get("position")


def get_teammate_h2h():
    """
    Build the complete teammate head-to-head comparison for the current season.

    Returns a dict with per-constructor H2H data covering qualifying,
    sprint qualifying, sprint race, main race, and standings delta.
    """
    current_year = str(datetime.now(timezone.utc).year)

    # --- Build driver → constructor mapping ---
    constructor_drivers, driver_standings, constructor_names = _build_driver_constructor_map()

    # --- Only consider constructors with exactly 2 official drivers ---
    valid_constructors = {
        c_id: drivers for c_id, drivers in constructor_drivers.items()
        if len(drivers) == 2
    }

    # --- Get completed rounds ---
    schedule_data = get_schedule()
    completed_rounds = [r for r in schedule_data["schedule"] if r.get("is_completed")]

    # --- Build H2H for each constructor ---
    h2h_results = []

    for c_id, drivers in valid_constructors.items():
        # Sort alphabetically by driver_id for deterministic ordering
        drivers_sorted = sorted(drivers, key=lambda d: d["driver_id"])
        driver_a = drivers_sorted[0]
        driver_b = drivers_sorted[1]
        da_id = driver_a["driver_id"]
        db_id = driver_b["driver_id"]

        # Accumulators for each section
        quali_data = {"driver_a_wins": 0, "driver_b_wins": 0, "ties": 0, "rounds": []}
        sprint_quali_data = {"driver_a_wins": 0, "driver_b_wins": 0, "ties": 0, "rounds": []}
        sprint_race_data = {"driver_a_wins": 0, "driver_b_wins": 0, "ties": 0, "rounds": []}
        race_data = {"driver_a_wins": 0, "driver_b_wins": 0, "ties": 0, "rounds": []}

        for r_entry in completed_rounds:
            rnd = str(r_entry["round"])
            race_name = r_entry["racename"]
            is_sprint = r_entry.get("is_sprint_weekend", False)

            round_data = get_round_results(current_year, rnd)

            # ---- Qualifying ----
            quali_positions = {}
            for qr in round_data["qualifying_results"]:
                d_id = qr["Driver"]["driverId"]
                quali_positions[d_id] = qr.get("position")

            result = _compare_session(da_id, db_id, quali_positions)
            if result:
                a_pos, b_pos, winner = result
                quali_data["rounds"].append({
                    "round": rnd,
                    "race_name": race_name,
                    "driver_a_position": a_pos,
                    "driver_b_position": b_pos,
                    "winner": winner,
                })
                if winner == "driver_a":
                    quali_data["driver_a_wins"] += 1
                elif winner == "driver_b":
                    quali_data["driver_b_wins"] += 1
                else:
                    quali_data["ties"] += 1

            # ---- Sprint Qualifying (derived from sprint grid) ----
            if is_sprint and round_data["sprint_results"]:
                sprint_grid_positions = {}
                for sr in round_data["sprint_results"]:
                    d_id = sr["Driver"]["driverId"]
                    grid_pos = sr.get("grid")
                    if grid_pos and grid_pos != "0":
                        sprint_grid_positions[d_id] = grid_pos

                result = _compare_session(da_id, db_id, sprint_grid_positions)
                if result:
                    a_pos, b_pos, winner = result
                    sprint_quali_data["rounds"].append({
                        "round": rnd,
                        "race_name": race_name,
                        "driver_a_position": a_pos,
                        "driver_b_position": b_pos,
                        "winner": winner,
                    })
                    if winner == "driver_a":
                        sprint_quali_data["driver_a_wins"] += 1
                    elif winner == "driver_b":
                        sprint_quali_data["driver_b_wins"] += 1
                    else:
                        sprint_quali_data["ties"] += 1

            # ---- Sprint Race ----
            if is_sprint and round_data["sprint_results"]:
                sprint_finish_positions = {}
                for sr in round_data["sprint_results"]:
                    d_id = sr["Driver"]["driverId"]
                    sprint_finish_positions[d_id] = sr.get("position")

                result = _compare_session(da_id, db_id, sprint_finish_positions)
                if result:
                    a_pos, b_pos, winner = result
                    sprint_race_data["rounds"].append({
                        "round": rnd,
                        "race_name": race_name,
                        "driver_a_position": a_pos,
                        "driver_b_position": b_pos,
                        "winner": winner,
                    })
                    if winner == "driver_a":
                        sprint_race_data["driver_a_wins"] += 1
                    elif winner == "driver_b":
                        sprint_race_data["driver_b_wins"] += 1
                    else:
                        sprint_race_data["ties"] += 1

            # ---- Main Race ----
            race_finish_positions = {}
            for rr in round_data["race_results"]:
                d_id = rr["Driver"]["driverId"]
                race_finish_positions[d_id] = rr.get("position")

            result = _compare_session(da_id, db_id, race_finish_positions)
            if result:
                a_pos, b_pos, winner = result
                race_data["rounds"].append({
                    "round": rnd,
                    "race_name": race_name,
                    "driver_a_position": a_pos,
                    "driver_b_position": b_pos,
                    "winner": winner,
                })
                if winner == "driver_a":
                    race_data["driver_a_wins"] += 1
                elif winner == "driver_b":
                    race_data["driver_b_wins"] += 1
                else:
                    race_data["ties"] += 1

        # ---- Standings delta ----
        da_standing = driver_standings.get(da_id, {"position": "N/A", "points": "0"})
        db_standing = driver_standings.get(db_id, {"position": "N/A", "points": "0"})

        try:
            points_delta = abs(float(da_standing["points"]) - float(db_standing["points"]))
        except (ValueError, TypeError):
            points_delta = 0.0

        try:
            positions_delta = abs(int(da_standing["position"]) - int(db_standing["position"]))
        except (ValueError, TypeError):
            positions_delta = 0

        # ---- Assemble constructor entry ----
        def _section_summary(data):
            return {
                "driver_a_wins": data["driver_a_wins"],
                "driver_b_wins": data["driver_b_wins"],
                "ties": data["ties"],
                "total_completed": len(data["rounds"]),
                "rounds": data["rounds"],
            }

        h2h_results.append({
            "constructor": constructor_names.get(c_id, "Unknown"),
            "constructor_id": c_id,
            "constructor_logo": get_constructor_logo(c_id),
            "drivers": {
                "driver_a": driver_a,
                "driver_b": driver_b,
            },
            "qualifying": _section_summary(quali_data),
            "sprint_qualifying": _section_summary(sprint_quali_data),
            "sprint_race": _section_summary(sprint_race_data),
            "race": _section_summary(race_data),
            "standings": {
                "driver_a": da_standing,
                "driver_b": db_standing,
                "points_delta": round(points_delta, 1),
                "positions_delta": positions_delta,
            },
        })

    # Sort by constructor name for consistent output
    h2h_results.sort(key=lambda x: x["constructor"])

    return {
        "season": current_year,
        "total_teams": len(h2h_results),
        "head_to_head": h2h_results,
    }
