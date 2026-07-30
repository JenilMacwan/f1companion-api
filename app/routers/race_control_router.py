"""
Race Control router.

Endpoint: /race_control
"""

from fastapi import APIRouter, HTTPException, Query
import requests

from app.services.race_control_service import get_race_control_messages

router = APIRouter()

@router.get("/race_control")
def race_control(session_key: str = Query("latest", description="The session key (e.g., 'latest' or '9158')")):
    try:
        return get_race_control_messages(session_key=session_key)
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching race control messages: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing race control messages: {str(e)}"
        )
