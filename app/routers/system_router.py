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
            {"path": "/", "description": "API Index"},
            {"path": "/schedule", "description": "Current season calendar"},
            {"path": "/next_race", "description": "Live countdown and track weather"},
            {"path": "/drivers", "description": "Current driver lineup"},
            {"path": "/constructors", "description": "Current team lineup"},
            {"path": "/driver_standings", "description": "WDC Live Standings"},
            {"path": "/constructor_standings", "description": "WCC Live Standings"},
            {"path": "/circuits", "description": "Information of all 2026 circuits"},
            {"path": "/race_results/{race_id}/{year}", "description": "Results of a specific race"},
            {"path": "/driver_stats", "description": "Deep career stats for drivers"},
            {"path": "/constructor_stats", "description": "Team performance and history"},
            {"path": "/news", "description": "Latest F1 news"}
        ],
        "status": "online"
    }


@router.get("/health")
def health_check():
    return {"status": "healthy"}


@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(str(FAVICON_PATH))
