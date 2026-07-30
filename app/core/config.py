"""
Application configuration and API URLs.

Contains all external API endpoints, CORS settings, and environment configuration.
This file should only contain configuration values — no business logic.
"""

from dotenv import load_dotenv
import os

load_dotenv()

IMAGE_BASE_URL = os.getenv("IMAGE_BASE_URL")
SCHEDULE_URL = os.getenv("SCHEDULE_URL")
DRIVERS_URL = os.getenv("DRIVERS_URL")
CONSTRUCTORS_URL = os.getenv("CONSTRUCTORS_URL")
DRIVER_STANDINGS_URL = os.getenv("DRIVER_STANDINGS_URL")
CONSTRUCTOR_STANDINGS_URL = os.getenv("CONSTRUCTOR_STANDINGS_URL")
PRIMARY_RSS_URL = os.getenv("PRIMARY_RSS_URL")
SECONDARY_RSS_URL = os.getenv("SECONDARY_RSS_URL")
FALLBACK_RSS_URL = os.getenv("FALLBACK_RSS_URL")
OPEN_METEO_BASE_URL = os.getenv("OPEN_METEO_BASE_URL")
STATS_BASE_URL = os.getenv("STATS_BASE_URL", "https://api.jolpi.ca/ergast/f1")
OPENF1_BASE_URL = os.getenv("OPENF1_BASE_URL", "https://api.openf1.org/v1")

# --- CORS Configuration ---
CORS_ORIGINS = ["*"]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# --- Application Metadata ---
APP_TITLE = "F1 Companion API 🏎️"
APP_VERSION = "1.0.0"
