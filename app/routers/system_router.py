"""
System router.

Endpoints: /, /health, /favicon.ico
"""

from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse

router = APIRouter()

# Resolve the favicon path relative to this file's location
FAVICON_PATH = Path(__file__).resolve().parent.parent.parent / "assets" / "favicon" / "f1_companion_icon.png"
INDEX_HTML_PATH = Path(__file__).resolve().parent.parent / "templates" / "index.html"


import os

@router.get("/", response_class=HTMLResponse)
def read_root():
    with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
        content = f.read()
        
        # If in Vercel production, hide the race_control card
        if os.getenv("VERCEL") == "1":
            content = content.replace("</style>", "    a[href='/race_control'] { display: none !important; }\n    </style>")
            
        return HTMLResponse(content=content)


import time
from app.core.config import APP_VERSION, SCHEDULE_URL
from app.core.http_client import http_client

START_TIME = time.time()

@router.get("/health")
def health_check():
    uptime_seconds = int(time.time() - START_TIME)
    
    # Check if the external Ergast API is reachable
    try:
        # Use a short timeout to prevent the health check from hanging
        response = http_client.session.get(SCHEDULE_URL, timeout=2.0)
        response.raise_for_status()
        ergast_status = "online"
    except Exception as e:
        ergast_status = f"offline ({type(e).__name__})"
        
    overall_status = "healthy" if ergast_status == "online" else "degraded"
    
    return {
        "status": overall_status,
        "version": APP_VERSION,
        "uptime_seconds": uptime_seconds,
        "dependencies": {
            "jolpica_ergast_api": ergast_status
        }
    }


@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(str(FAVICON_PATH))
