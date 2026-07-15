"""
Static constants used across the application.

Contains weather code mappings, track layout URLs, session durations,
and country-to-ISO code mappings. These values are static and do not
belong inside route handlers or services.
"""

# --- WMO Weather Code Descriptions ---
# Used by the weather service to convert numeric codes to human-readable conditions.
WMO_CODES = {
    0: "Clear Sky",
    1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing Rime Fog",
    51: "Light Drizzle", 53: "Moderate Drizzle", 55: "Dense Drizzle",
    61: "Slight Rain", 63: "Moderate Rain", 65: "Heavy Rain",
    71: "Slight Snow", 73: "Moderate Snow", 75: "Heavy Snow",
    80: "Slight Rain Showers", 81: "Moderate Rain Showers", 82: "Violent Rain Showers",
    95: "Thunderstorm", 96: "Thunderstorm with Hail", 99: "Thunderstorm with Heavy Hail"
}

# --- Track Layout Image URLs ---
# Keyed by circuit locality name. Used by the /circuits endpoint.
TRACK_LAYOUT = {
    "Sakhir": "track/sakhir-bahrain2026.webp",
    "Melbourne": "track/australia-melbourne.webp",
    "Shanghai": "track/shanghai-china.webp",
    "Suzuka": "track/suzuka-japan.webp",
    "Montreal": "track/montreal-canada.webp",
    "Barcelona": "track/barcelona-spain.webp",
    "Spielberg": "track/speilberg-austri.webp",
    "Madrid": "track/madrid-spain.webp",
    "Silverstone": "track/silverstone-great-britain.webp",
    "Budapest": "track/hungary.webp",
    "Spa": "track/spa-belgium.webp",
    "Monza": "track/monza-italy.webp",
    "Baku": "track/baku-azerbaijan.webp",
    "Austin": "track/austin-usa.webp",
    "Mexico City": "track/mexico.webp",
    "São Paulo": "track/sao-paulo-brazil.webp",
    "Las Vegas": "track/lasvegas-usa.webp",
    "Lusail": "track/lusail-qatar.webp",
    "Abu Dhabi": "track/yasmarina-abudhabi.webp",
    "Monte Carlo": "track/monte-carlo-monaco.webp",
    "Miami": "track/maimi-usa.webp",
    "Zandvoort": "track/zandvoort-netherlands.webp",
    "Marina Bay": "track/marinabay-singapore.webp",
    "Jeddah": "track/jeddah-saudi.webp"
}

# --- Session Durations (in minutes) ---
# Used by the race service to determine if a session is still ongoing.
SESSION_DURATIONS = {
    "Practice 1": 60, "Practice 2": 60, "Practice 3": 60,
    "Qualifying": 60, "Sprint Qualifying": 45,
    "Sprint": 30, "Race": 120
}

# --- Country Name to ISO-2 Code Mapping ---
# F1 countries often use shorthand names; this maps them to ISO-2 codes for flag emoji.
COUNTRY_ISO_MAPPING = {
    "UK": "GB", "USA": "US", "UAE": "AE", "Netherlands": "NL",
    "Saudi Arabia": "SA", "Italy": "IT", "Japan": "JP", "Canada": "CA",
    "Australia": "AU", "Spain": "ES", "Austria": "AT", "Hungary": "HU",
    "Belgium": "BE", "Monaco": "MC", "Azerbaijan": "AZ", "Singapore": "SG",
    "Brazil": "BR", "Las Vegas": "US", "Bahrain": "BH", "Qatar": "QA",
    "China": "CN", "Monza": "IT", "Mexico": "MX", "Germany": "DE",
    "Portugal": "PT", "Turkey": "TR", "Malaysia": "MY", "South Africa": "ZA",
    "South Korea": "KR", "Sweden": "SE", "Switzerland": "CH", "France": "FR"
}

# --- Session Keys for Schedule Parsing ---
# Maps internal session keys to display names.
SESSION_KEYS = {
    "FirstPractice": "Practice 1",
    "SecondPractice": "Practice 2",
    "ThirdPractice": "Practice 3",
    "Qualifying": "Qualifying",
    "Sprint": "Sprint",
    "SprintQualifying": "Sprint Qualifying"
}

# --- Official 2026 Season Drivers ---
# Only contracted race seat holders. Filters out reserve/test/substitute drivers
# that Jolpica includes from practice or one-off race appearances.
OFFICIAL_DRIVERS_2026 = {
    "albon", "alonso", "antonelli", "bearman", "bortoleto",
    "bottas", "colapinto", "gasly", "hadjar",
    "hamilton", "hulkenberg", "lawson", "leclerc", "arvid_lindblad",
    "norris", "ocon", "piastri", "perez", "russell",
    "sainz", "stroll", "max_verstappen"
}

