"""
Weather service.

Responsible for fetching live weather data from the Open-Meteo API
and mapping weather codes to human-readable conditions.
"""

from app.core.constants import WMO_CODES
from app.core.http_client import http_client


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
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,weather_code&timezone=auto"
    )

    try:
        w_res = http_client.fetch_json(weather_url)
        return {
            "temp": f"{int(w_res['current']['temperature_2m'])}°C",
            "condition": WMO_CODES.get(
                w_res['current']['weather_code'], "Unknown"
            )
        }
    except Exception as e:
        return {"temp": "N/A", "condition": "Unknown", "error": str(e)}
