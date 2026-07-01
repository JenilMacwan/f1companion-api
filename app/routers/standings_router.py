"""
Standings router.

Endpoints: /driver_standings, /constructor_standings
"""

from fastapi import APIRouter, HTTPException

from app.services.standings_service import get_driver_standings, get_constructor_standings

router = APIRouter()


@router.get("/driver_standings")
def driver_standings():
    try:
        return get_driver_standings()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"API Error: {str(e)}"
        )


@router.get("/constructor_standings")
def constructor_standings():
    try:
        return get_constructor_standings()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"API Error: {str(e)}"
        )
