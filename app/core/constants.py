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
    "Sakhir": "https://github.com/JenilMacwan/f1companion-api/blob/997e3c439135be7d4fcf47fb050d66ce23e96921/assests/track/sakhir-bahrain2026.webp?raw=true",
    "Melbourne": "https://github.com/JenilMacwan/f1companion-api/blob/5b7986d8e6ea48f9de6e93a548caf5e156f10369/assets/track/australia-melbourne.webp?raw=true",
    "Shanghai": "https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/shanghai-china.webp?raw=true",
    "Suzuka": "https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/suzuka-japan.webp?raw=true",
    "Montreal": "https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/monteeal%20-%20canada.webp?raw=true",
    "Barcelona": "https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/barcelona%20-%20spain.webp?raw=true",
    "Spielberg": "https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/speilberg%20-%20austri.webp?raw=true",
    "Madrid": "https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/madrid%20-%20spain.webp?raw=true",
    "Silverstone": "https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/silverstone%20-%20great%20britain.webp?raw=true",
    "Budapest": "https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/hungary.webp?raw=true",
    "Spa": "https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/spa%20-%20belgium.webp?raw=true",
    "Monza": "https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/monza%20-%20italy.webp?raw=true",
    "Baku": "https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/baku-azerbaijan.webp?raw=true",
    "Austin": "https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/austin-usa.webp?raw=true",
    "Mexico City": "https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/mexico.webp?raw=true",
    "São Paulo": "https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/sao%20paulo%20-%20brazil.webp?raw=true",
    "Las Vegas": "https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/lasvegas%20-%20usa.webp?raw=true",
    "Lusail": "https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/lusail-qatar.webp?raw=true",
    "Abu Dhabi": "https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/yasmarina%20-%20abudhabi.webp?raw=true",
    "Monte Carlo": "https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/monte%20carlo%20-%20monaco.webp?raw=true",
    "Miami": "https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/maimi-usa.webp?raw=true",
    "Zandvoort": "https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/zandvoort%20-%20netherlands.webp?raw=true",
    "Marina Bay": "https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/marinabay-singapore.webp?raw=true",
    "Jeddah": "https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/jeddah-saudi.webp?raw=true"
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
