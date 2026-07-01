"""
Driver service.

Responsible for fetching and processing driver information.
"""

from app.core.config import DRIVERS_URL
from app.core.http_client import http_client


def get_drivers():
    """
    Fetch and clean the current season's driver lineup.

    Returns:
        Dict with season, total driver count, and cleaned drivers list.

    Raises:
        requests.exceptions.RequestException: On API fetch failure.
    """
    data = http_client.fetch_json(DRIVERS_URL)
    drivers_raw = data["MRData"]["DriverTable"]["Drivers"]

    clean_drivers = []
    for driver in drivers_raw:
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
