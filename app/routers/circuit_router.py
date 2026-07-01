"""
Circuit router.

Endpoint: /circuits
"""

from fastapi import APIRouter, HTTPException
import requests

from app.core.config import F1_SCHEDULE_URL
from app.core.constants import TRACK_LAYOUT
from app.core.http_client import http_client

router = APIRouter()


@router.get("/circuits")
def circuits():
    try:
        data = http_client.fetch_json(F1_SCHEDULE_URL)
        circuits_raw = data["MRData"]["RaceTable"]["Races"]

        clean_circuits = []
        for race in circuits_raw:
            country_name = race["Circuit"]["Location"]["country"]
            country_locality = race["Circuit"]["Location"]["locality"]
            layout_url = TRACK_LAYOUT.get(country_locality, "N/A")
            circuit_entry = {
                "circuitid": race["Circuit"]["circuitId"],
                "circuitname": race["Circuit"]["circuitName"],
                "circuitlocation": country_locality,
                "circuitcountry": country_name,
                "circuitlayout": layout_url
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
