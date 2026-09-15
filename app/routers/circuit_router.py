"""
Circuit router.

Endpoint: /circuits
"""

from fastapi import APIRouter, HTTPException
import requests

from app.core.config import SCHEDULE_URL
from app.core.constants import CIRCUIT_STATS
from app.core.http_client import http_client
from app.utils.helpers import get_track_layout

router = APIRouter()


@router.get("/circuits")
def circuits():
    try:
        data = http_client.fetch_json(SCHEDULE_URL)
        circuits_raw = data["MRData"]["RaceTable"]["Races"]

        clean_circuits = []
        for race in circuits_raw:
            country_name = race["Circuit"]["Location"]["country"]
            country_locality = race["Circuit"]["Location"]["locality"]
            layout_url = get_track_layout(country_locality)
            circuit_id = race["Circuit"]["circuitId"]
            stats = CIRCUIT_STATS.get(circuit_id, {"laps": "N/A", "length": "N/A"})

            circuit_entry = {
                "circuitid": circuit_id,
                "circuitname": race["Circuit"]["circuitName"],
                "circuitlocation": country_locality,
                "circuitcountry": country_name,
                "circuitlayout": layout_url,
                "laps": stats.get("laps", "N/A"),
                "length": stats.get("length", "N/A"),
                "type": stats.get("type", "N/A")
            }
            clean_circuits.append(circuit_entry)

        return {
            "season": data["MRData"]["RaceTable"]["season"],
            "total_circuits": len(clean_circuits),
            "circuits": clean_circuits
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching F1 circuits: {str(e)}"
        )
