"""
Stats service.

Responsible for driver career statistics, constructor statistics,
championship calculations, and dynamic yearly updates.
"""

from datetime import datetime, timezone
from app.core.http_client import http_client
from app.core.logging import logger
from app.core.config import STATS_BASE_URL
from app.data.championships import (
    GLOBAL_WDC_MAP, GLOBAL_WCC_MAP, GLOBAL_DRIVER_WCC_MAP, UPDATED_YEARS
)
from app.data.driver_stats import DRIVER_BASE_STATS
from app.data.constructor_stats import CONSTRUCTOR_BASE_STATS
from app.utils.helpers import stats

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
                stats(f"{year}/driverStandings.json")
            )
            if r1:
                st1 = r1["MRData"]["StandingsTable"]["StandingsLists"]
                if st1:
                    d_id = st1[0]["DriverStandings"][0]["Driver"]["driverId"]
                    c_id = st1[0]["DriverStandings"][0]["Constructors"][0]["constructorId"]
                    GLOBAL_WDC_MAP[d_id] = GLOBAL_WDC_MAP.get(d_id, 0) + 1
                    GLOBAL_DRIVER_WCC_MAP[c_id] = GLOBAL_DRIVER_WCC_MAP.get(c_id, 0) + 1

            r2 = http_client.fetch_json_safe(
                stats(f"{year}/constructorStandings.json")
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

