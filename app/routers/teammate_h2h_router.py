"""
Teammate head-to-head router.

Endpoints: /teammate_h2h
"""

from fastapi import APIRouter, HTTPException

from app.services.teammate_h2h_service import get_teammate_h2h

router = APIRouter()


@router.get("/teammate_h2h")
def teammate_h2h():
    try:
        return get_teammate_h2h()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching teammate head-to-head data: {str(e)}"
        )
