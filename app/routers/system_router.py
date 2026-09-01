"""
System router.

Endpoints: /, /health, /favicon.ico
"""

from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, Response

router = APIRouter()

# Resolve the favicon path relative to this file's location
FAVICON_PATH = Path(__file__).resolve().parent.parent.parent / "assets" / "favicon" / "f1_companion_icon.png"
INDEX_HTML_PATH = Path(__file__).resolve().parent.parent / "templates" / "index.html"
API_DOCS_HTML_PATH = Path(__file__).resolve().parent.parent / "templates" / "api_docs.html"


import os

@router.get("/", response_class=HTMLResponse)
def read_root():
    with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
        content = f.read()
        
        # If in Vercel production, hide the race_control card
        if os.getenv("VERCEL") == "1":
            content = content.replace("</style>", "    a[href='/race_control'] { display: none !important; }\n    </style>")
            
        return HTMLResponse(content=content)


@router.get("/api-docs", response_class=HTMLResponse)
def api_docs():
    with open(API_DOCS_HTML_PATH, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


import time
from app.core.config import APP_VERSION, SCHEDULE_URL
from app.core.http_client import http_client

START_TIME = time.time()

ROBOTS_TXT_CONTENT = """User-agent: *
Allow: /

Sitemap: https://f1-companion-api-ba5k.onrender.com/sitemap.xml
"""

SITEMAP_XML_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://f1-companion-api-ba5k.onrender.com/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://f1-companion-api-ba5k.onrender.com/api-docs</loc>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
</urlset>
"""

@router.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    return PlainTextResponse(content=ROBOTS_TXT_CONTENT)


@router.get("/sitemap.xml")
def sitemap_xml():
    return Response(content=SITEMAP_XML_CONTENT, media_type="application/xml")


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
        
    # Check if the OpenF1 API is reachable
    from app.core.config import OPENF1_BASE_URL
    try:
        openf1_response = http_client.session.get(f"{OPENF1_BASE_URL}/sessions?session_key=latest", timeout=2.0)
        openf1_response.raise_for_status()
        openf1_status = "online"
    except Exception as e:
        openf1_status = f"offline ({type(e).__name__})"
        
    # Get active WebSocket connections
    from app.core.websocket_manager import websocket_manager
    active_websockets = len(websocket_manager.active_connections)
        
    overall_status = "healthy" if (ergast_status == "online" and openf1_status == "online") else "degraded"
    
    return {
        "status": overall_status,
        "version": APP_VERSION,
        "uptime_seconds": uptime_seconds,
        "active_websockets": active_websockets,
        "dependencies": {
            "jolpica_ergast_api": ergast_status,
            "openf1_api": openf1_status
        }
    }


@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(str(FAVICON_PATH))
