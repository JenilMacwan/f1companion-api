"""
Round results service.

Fetches and caches the FULL season's race + sprint results using two
bulk calls per season (not per-round) — matching Jolpica's own
guidance to query a whole season at once rather than round-by-round,
which avoids their 4 req/sec burst limit entirely instead of trying
to pace around it.

Cached in-process per season for TTL_SECONDS. A cache miss (first
request after a cold start, or after the TTL expires) triggers a
fresh bulk fetch; every other request during that window is served
from memory with zero upstream calls.
"""

import threading
import time
from app.core.http_client import http_client
from app.core.logging import logger
from app.utils.helpers import stats

TTL_SECONDS = 45 * 60  # refresh the cached season data at most every 45 minutes

# {year: {"race_results_by_round": {...}, "sprint_results_by_round": {...}, "fetched_at": float}}
_cache = {}
_lock = threading.Lock()


def _fetch_season_bulk(current_year):
    """
    Fetch the full season's race + sprint results using paginated calls
    (the Jolpica API hard-caps responses at 100 result rows regardless of
    the ``limit`` query-param) and index each by round number.

    Returns:
        Dict: {
            "race_results_by_round": {round_str: [Results...]},
            "sprint_results_by_round": {round_str: [SprintResults...]},
        }
    """
    PAGE_SIZE = 100  # Jolpica hard cap

    # --- Race results (paginated) ---
    race_results_by_round = {}
    offset = 0
    while True:
        try:
            url = stats(f"{current_year}/results.json?limit={PAGE_SIZE}&offset={offset}")
            res = http_client.fetch_json_safe(url)
            if not res:
                break
            total = int(res["MRData"].get("total", "0"))
            races = res["MRData"]["RaceTable"]["Races"]
            for race in races:
                rnd = str(race["round"])
                # Merge results into existing round entry (a round can be
                # split across two pages if it straddles the 100-row boundary).
                existing = race_results_by_round.get(rnd, [])
                existing.extend(race.get("Results", []))
                race_results_by_round[rnd] = existing
            offset += PAGE_SIZE
            if offset >= total:
                break
        except Exception:
            logger.warning(f"Failed to fetch race results page offset={offset} for {current_year}")
            break

    # --- Sprint results (paginated) ---
    sprint_results_by_round = {}
    offset = 0
    while True:
        try:
            url = stats(f"{current_year}/sprint.json?limit={PAGE_SIZE}&offset={offset}")
            res = http_client.fetch_json_safe(url)
            if not res:
                break
            total = int(res["MRData"].get("total", "0"))
            sprints = res["MRData"]["RaceTable"]["Races"]
            for race in sprints:
                rnd = str(race["round"])
                existing = sprint_results_by_round.get(rnd, [])
                existing.extend(race.get("SprintResults", []))
                sprint_results_by_round[rnd] = existing
            offset += PAGE_SIZE
            if offset >= total:
                break
        except Exception:
            logger.warning(f"Failed to fetch sprint results page offset={offset} for {current_year}")
            break

    return {
        "race_results_by_round": race_results_by_round,
        "sprint_results_by_round": sprint_results_by_round,
    }



def _get_season_cache(current_year):
    """
    Return cached season bulk data, refreshing it if missing or stale.

    The fetch happens while holding the lock so that a burst of
    concurrent requests arriving right as the TTL expires (a "cache
    stampede") wait for a single fetch instead of each independently
    triggering their own bulk call to Jolpica.
    """
    with _lock:
        cached = _cache.get(current_year)
        now = time.monotonic()

        if cached is not None and (now - cached["fetched_at"]) < TTL_SECONDS:
            return cached

        fresh = _fetch_season_bulk(current_year)
        fresh["fetched_at"] = time.monotonic()
        _cache[current_year] = fresh
        return fresh


def get_round_results(current_year, rnd):
    """
    Return race + sprint results for a single round, sourced from the
    cached season-wide bulk fetch (refreshed at most every TTL_SECONDS).

    A round absent from the bulk race-results response means Jolpica
    has not published results for it yet — race_data_available is
    False in that case, so callers can skip the round entirely rather
    than treat it as a driver/constructor scoring 0 points.

    Returns:
        Dict:
        {
            "race_results": [...],    # raw Results list for this round, or []
            "sprint_results": [...],  # raw SprintResults list for this round, or []
            "race_data_available": bool
        }
    """
    season_data = _get_season_cache(current_year)

    race_results = season_data["race_results_by_round"].get(rnd)
    sprint_results = season_data["sprint_results_by_round"].get(rnd, [])

    return {
        "race_results": race_results or [],
        "sprint_results": sprint_results,
        "race_data_available": race_results is not None
    }


def clear_cache():
    """Clear all cached season results. Useful for tests or manual invalidation."""
    with _lock:
        _cache.clear()