"""
Constructor router.

Endpoint: /constructors
"""

from fastapi import APIRouter, HTTPException
import requests

from app.services.constructor_service import get_constructors

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
