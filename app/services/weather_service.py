"""
Weather service.

Responsible for fetching live weather data from the Open-Meteo API
and mapping weather codes to human-readable conditions.
"""

import time
from app.core.constants import WMO_CODES
from app.core.http_client import http_client
from app.core.config import OPEN_METEO_BASE_URL

_weather_cache = {}
CACHE_TTL = 30 * 60  # 30 minutes in seconds

def get_track_weather(lat, lon):
    """
    Fetch current weather conditions at a circuit location.

    Args:
        lat: Latitude of the circuit.
        lon: Longitude of the circuit.

    Returns:
        Dict with 'temp' and 'condition' keys.
        Returns fallback values on failure.
    """
    cache_key = f"{lat},{lon}"
    current_time = time.time()

    if cache_key in _weather_cache:
        cached_data, timestamp = _weather_cache[cache_key]
        if current_time - timestamp < CACHE_TTL:
            return cached_data

    weather_url = (
        f"{OPEN_METEO_BASE_URL}/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,surface_temperature,weather_code&timezone=auto"
    )

    try:
        w_res = http_client.fetch_json(weather_url)
        data = {
            "temp": f"{int(w_res['current']['temperature_2m'])}°C",
            "track_temp": f"{int(w_res['current']['surface_temperature'])}°C",
            "condition": WMO_CODES.get(
                w_res['current']['weather_code'], "Unknown"
            )
        }
        _weather_cache[cache_key] = (data, current_time)
        return data
    except Exception as e:
        data = {"temp": "N/A", "track_temp": "N/A", "condition": "Unknown", "error": str(e)}
        _weather_cache[cache_key] = (data, current_time)
        return data
