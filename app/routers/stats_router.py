"""
Stats router.

Endpoints: /driver_stats, /constructor_stats
"""

from fastapi import APIRouter, HTTPException

from app.services.stats_service import get_driver_stats, get_constructor_stats

router = APIRouter()


@router.get("/driver_stats")
def driver_stats():
    try:
        return get_driver_stats()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"API Error: {str(e)}"
        )


@router.get("/constructor_stats")
def constructor_stats():
    try:
        return get_constructor_stats()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing stats: {str(e)}"
        )
