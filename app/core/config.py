"""
Application configuration and API URLs.

Contains all external API endpoints, CORS settings, and environment configuration.
This file should only contain configuration values — no business logic.
"""

# --- Jolpica Ergast API URLs ---
F1_SCHEDULE_URL = "https://api.jolpi.ca/ergast/f1/2026.json"
DRIVER_STANDINGS_URL = "https://api.jolpi.ca/ergast/f1/2026/driverstandings.json"
CONSTRUCTOR_STANDINGS_URL = "https://api.jolpi.ca/ergast/f1/2026/constructorstandings.json"
DRIVERS_URL = "https://api.jolpi.ca/ergast/f1/2026/drivers.json"
CONSTRUCTORS_URL = "https://api.jolpi.ca/ergast/f1/2026/constructors.json"

# --- CORS Configuration ---
CORS_ORIGINS = ["*"]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# --- Application Metadata ---
APP_TITLE = "F1 Companion API 🏎️"
APP_VERSION = "1.0.0"
