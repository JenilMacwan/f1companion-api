"""
F1 Companion API — Main Application Entry Point.

"""

import sys
from pathlib import Path

_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import (
    CORS_ORIGINS,
    CORS_ALLOW_CREDENTIALS,
    CORS_ALLOW_METHODS,
    CORS_ALLOW_HEADERS,
)
from app.routers import (
    system_router,
    schedule_router,
    race_router,
    driver_router,
    constructor_router,
    standings_router,
    circuit_router,
    news_router,
    race_control_router,
)

# --- Create Application ---
app = FastAPI()

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)

# --- Register Routers ---
app.include_router(system_router.router)
app.include_router(schedule_router.router)
app.include_router(race_router.router)
app.include_router(driver_router.router)
app.include_router(constructor_router.router)
app.include_router(standings_router.router)
app.include_router(circuit_router.router)
app.include_router(news_router.router)

# Exclude race_control endpoint in Vercel production environment
import os
if os.getenv("VERCEL") != "1":
    app.include_router(race_control_router.router)

# --- Local Development ---
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=5000, reload=True)
