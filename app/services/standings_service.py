"""
Standings service.

Responsible for fetching and processing driver and constructor championship standings.
"""

from app.core.config import DRIVER_STANDINGS_URL, CONSTRUCTOR_STANDINGS_URL
from app.core.http_client import http_client


def get_driver_standings():
    """
    Fetch and clean the live WDC (World Drivers' Championship) standings.

    Returns:
        Dict with season, status, total drivers, and standings list.

    Raises:
        Exception: On API or processing failure.
    """
    data = http_client.fetch_json(DRIVER_STANDINGS_URL)
    standings_lists = data["MRData"]["StandingsTable"]["StandingsLists"]

    # Check if the list is empty (season not started)
    if not standings_lists:
        return {
            "season": data["MRData"]["StandingsTable"]["season"],
            "status": "SEASON IS YET TO BEGIN",
            "drivers": []
        }

    drivers_raw = standings_lists[0]["DriverStandings"]

    clean_drivers = []
    for item in drivers_raw:
        driver_data = item.get("Driver", {})
        constructors = item.get("Constructors", [])
        constructor_name = constructors[0].get("name", "N/A") if constructors else "N/A"
        clean_drivers.append({
            "position": item.get("position"),
            "points": item.get("points"),
            "driverid": driver_data.get("driverId"),
            "name": f"{driver_data.get('givenName')} {driver_data.get('familyName')}",
            "team_name": constructor_name,
            "nationality": driver_data.get("nationality", "N/A"),
            "url": driver_data.get("url", "No URL")
        })

    return {
        "season": data["MRData"]["StandingsTable"]["season"],
        "status": "SEASON IN PROGRESS",
        "total_drivers": len(clean_drivers),
        "drivers": clean_drivers
    }


def get_constructor_standings():
    """
    Fetch and clean the live WCC (World Constructors' Championship) standings.

    Also fetches driver standings to map which drivers belong to each constructor.

    Returns:
        Dict with season, status, total teams, and standings list.

    Raises:
        Exception: On API or processing failure.
    """
    data = http_client.fetch_json(CONSTRUCTOR_STANDINGS_URL)
    standings_lists = data["MRData"]["StandingsTable"]["StandingsLists"]

    # Check if the list is empty (season not started)
    if not standings_lists:
        return {
            "season": data["MRData"]["StandingsTable"]["season"],
            "status": "SEASON IS YET TO BEGIN",
            "constructors": []
        }

    # Fetch driver standings to map drivers to constructors
    driver_data = http_client.fetch_json(DRIVER_STANDINGS_URL)
    driver_standings_lists = driver_data["MRData"]["StandingsTable"]["StandingsLists"]

    constructor_drivers = {}
    if driver_standings_lists:
        for d_item in driver_standings_lists[0]["DriverStandings"]:
            driver_info = d_item.get("Driver", {})
            d_name = f"{driver_info.get('givenName')} {driver_info.get('familyName')}"
            for c in d_item.get("Constructors", []):
                c_id = c.get("constructorId")
                if c_id not in constructor_drivers:
                    constructor_drivers[c_id] = []
                constructor_drivers[c_id].append(d_name)

    # Clean constructor standings
    standing_raw = standings_lists[0]["ConstructorStandings"]
    clean_constructors = []
    for item in standing_raw:
        cons_data = item.get("Constructor", {})
        c_id = cons_data.get("constructorId")
        drivers = constructor_drivers.get(c_id, [])
        clean_constructors.append({
            "position": item.get("position"),
            "points": item.get("points"),
            "name": cons_data.get("name", "Unknown"),
            "drivers": drivers if drivers else "N/A",
            "nationality": cons_data.get("nationality", "N/A")
        })

    return {
        "season": data["MRData"]["StandingsTable"]["season"],
        "status": "SEASON IN PROGRESS",
        "total_teams": len(clean_constructors),
        "constructors": clean_constructors
    }
