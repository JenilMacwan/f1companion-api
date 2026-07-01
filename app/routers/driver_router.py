"""
Driver router.

Endpoint: /drivers
"""

from fastapi import APIRouter, HTTPException
import requests

from app.services.driver_service import get_drivers

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
