"""
Constructor router.

Endpoints: /constructors, /constructor_profile
"""

from fastapi import APIRouter, HTTPException
import requests

from app.services.constructor_service import get_constructors, get_constructor_profiles

router = APIRouter()


@router.get("/constructors")
def constructors():
    try:
        return get_constructors()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


@router.get("/constructor_profile")
def constructor_profile():
    try:
        return get_constructor_profiles()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching constructor profiles: {str(e)}"
        )
