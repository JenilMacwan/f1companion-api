"""
Driver router.

Endpoints: /drivers, /driver_profile
"""

from fastapi import APIRouter, HTTPException
import requests

from app.services.driver_service import get_drivers, get_driver_profiles

router = APIRouter()


@router.get("/drivers")
def drivers():
    try:
        return get_drivers()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


@router.get("/driver_profile")
def driver_profile():
    try:
        return get_driver_profiles()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching driver profiles: {str(e)}"
        )
