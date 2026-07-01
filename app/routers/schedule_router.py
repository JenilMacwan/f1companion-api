"""
Schedule router.

Endpoint: /schedule
"""

from fastapi import APIRouter, HTTPException
import requests

from app.services.schedule_service import get_schedule

router = APIRouter()


@router.get("/schedule")
def schedule():
    try:
        return get_schedule()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching F1 schedule: {str(e)}"
        )
