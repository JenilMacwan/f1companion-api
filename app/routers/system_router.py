"""
System router.

Endpoints: /, /health, /favicon.ico
"""

from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

# Resolve the favicon path relative to this file's location
FAVICON_PATH = Path(__file__).resolve().parent.parent.parent / "assets" / "favicon" / "f1_companion_icon.png"


@router.get("/")
def read_root():
    return {
        "title": "F1 Companion API 🏎️",
        "welcome_message": "Welcome to the F1 Companion API",
        "description": "A high-performance middleware for Formula 1 data.",
        "endpoints": [
            {"path": "/", "description": "API Index — lists all available endpoints"},
            {"path": "/schedule", "description": "Full season calendar with race dates and session times"},
            {"path": "/next_race", "description": "Next upcoming race with live countdown, session info, and track weather"},
            {"path": "/circuits", "description": "All circuit details with track layout images"},
            {"path": "/drivers", "description": "Current season driver lineup (lightweight)"},
            {"path": "/driver_profile", "description": "Enriched driver profiles with image, team, and full career statistics"},
            {"path": "/constructors", "description": "Current season constructor/team lineup (lightweight)"},
            {"path": "/constructor_profile", "description": "Enriched constructor profiles with logo, drivers, and full career statistics"},
            {"path": "/driver_standings", "description": "Live World Drivers' Championship standings"},
            {"path": "/constructor_standings", "description": "Live World Constructors' Championship standings"},
            {"path": "/race_results/{round}/{year}", "description": "Detailed results for a specific race by round and year"},
            {"path": "/news", "description": "Latest F1 news aggregated from multiple sources"},
            {"path": "/health", "description": "API health check"}
        ],
        "status": "online"
    }


@router.get("/health")
def health_check():
    return {"status": "healthy"}


@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(str(FAVICON_PATH))
