"""
Race router.

Endpoints: /next_race, /race_results/{round}/{year}
"""

from fastapi import APIRouter, HTTPException
import requests

from app.services.race_service import get_next_race, get_race_results

router = APIRouter()


@router.get("/next_race")
def next_race():
    try:
        return get_next_race()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/race_results/{round}/{year}")
def race_results(round: str, year: str):
    try:
        return get_race_results(round, year)
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching F1 races: {str(e)}"
        )
