import uvicorn
import flag
import concurrent.futures
import requests
import feedparser
import re
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all domains (perfect for testing)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app = app

F1COMPNAION = "https://api.jolpi.ca/ergast/f1/2026.json"

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

TRACK_LAYOUT = {
    "Sakhir": "https://github.com/JenilMacwan/f1companion-api/blob/997e3c439135be7d4fcf47fb050d66ce23e96921/assests/track/sakhir-bahrain2026.webp?raw=true",
    "Melbourne":"https://github.com/JenilMacwan/f1companion-api/blob/5b7986d8e6ea48f9de6e93a548caf5e156f10369/assets/track/australia-melbourne.webp?raw=true",
    "Shanghai":"https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/shanghai-china.webp?raw=true",
    "Suzuka":"https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/suzuka-japan.webp?raw=true",
    "Montreal":"https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/monteeal%20-%20canada.webp?.raw=true",
    "Barcelona":"https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/barcelona%20-%20spain.webp",
    "Spielberg":"https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/speilberg%20-%20austri.webp",
    "Madrid":"https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/madrid%20-%20spain.webp",
    "Silverstone":"https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/silverstone%20-%20great%20britain.webp",
    "Budapest":"https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/hungary.webp",
    "Spa":"https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/spa%20-%20belgium.webp",
    "Monza":"https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/monza%20-%20italy.webp",
    "Baku":"https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/baku-azerbaijan.webp",
    "Austin":"https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/austin-usa.webp",
    "Mexico City":"https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/mexico.webp",
    "São Paulo":"https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/sao%20paulo%20-%20brazil.webp",
    "Las Vegas":"https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/lasvegas%20-%20usa.webp",
    "Lusail":"https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/lusail-qatar.webp",
    "Abu Dhabi":"https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/yasmarina%20-%20abudhabi.webp",
    "Monte Carlo":"https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/monte%20carlo%20-%20monaco.webp",
    "Miami":"https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/maimi-usa.webp",
    "Zandvoort":"https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/zandvoort%20-%20netherlands.webp",
    "Marina Bay":"https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/marinabay-singapore.webp",
    "Jeddah":"https://github.com/JenilMacwan/f1companion-api/blob/b3467d8d473bb572f238ffc018b4dd34fbddf047/assets/track/jeddah-saudi.webp"
}


DRIVER_STANDINGS = "https://api.jolpi.ca/ergast/f1/2026/driverstandings.json"
CONS_STANDINGS = "https://api.jolpi.ca/ergast/f1/2026/constructorstandings.json"

DRIVERS = "https://api.jolpi.ca/ergast/f1/2026/drivers.json"
CONSTRUCTORS = "https://api.jolpi.ca/ergast/f1/2026/constructors.json"

@app.get("/")
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

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("assets/favicon/f1_companion_icon.png")

@app.get("/schedule")
def get_schedule():
    try:
        response = requests.get(F1COMPNAION)
        response.raise_for_status()
        data = response.json()

        races_raw = data["MRData"]["RaceTable"]["Races"]

        clean_schedule = []
        for race in races_raw:

            race_entry = {
                "round": race["round"],
                "racename": race["raceName"],
                "circuitid": race["Circuit"]["circuitId"],
                "circuitname": race["Circuit"]["circuitName"],
                "circuitlocation": race["Circuit"]["Location"]["locality"],
                "circuitcountry": race["Circuit"]["Location"]["country"],

                "GrandPrix": race["date"],
                "time": race.get("time", "TBA")
            }

            sessions = [
                "FirstPractice",
                "SecondPractice",
                "ThirdPractice",
                "Qualifying",
                "Sprint",
                "SprintQualifying"
            ]

            for session in sessions:
                session_data = race.get(session)
                if session_data:
                    race_entry[session] = {
                        "date": session_data.get("date"),
                        "time": session_data.get("time")
                    }

            clean_schedule.append(race_entry)

        return {
            "season": data["MRData"]["RaceTable"]["season"], 
            "races": len(clean_schedule), 
            "schedule": clean_schedule
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching F1 schedule: {str(e)}")

import requests
from datetime import datetime, timezone

@app.get("/next_race")
def get_next_race():
    try:
        # 1. Fetch Schedule
        response = requests.get(F1COMPNAION)
        response.raise_for_status()
        data = response.json()

        now = datetime.now(timezone.utc)
        races = data["MRData"]["RaceTable"]["Races"]
        
        next_event = None
        for race in races:
            # Check race date/time
            race_time_str = f"{race['date']}T{race.get('time', '00:00:00Z')}"
            race_dt = datetime.fromisoformat(race_time_str.replace('Z', '+00:00'))
            
            if race_dt > now:
                next_event = race
                break

        if not next_event:
            return {"message": "Season concluded."}

        # 2. Target Session for Countdown
        session_keys = {
            "FirstPractice": "Practice 1",
            "SecondPractice": "Practice 2",
            "ThirdPractice": "Practice 3",
            "Qualifying": "Qualifying",
            "Sprint": "Sprint",
            "SprintQualifying": "Sprint Qualifying"
        }
        
        sessions_list = [{"name": "Race", "dt": race_dt}]
        for key, name in session_keys.items():
            session = next_event.get(key)
            if session:
                s_str = f"{session['date']}T{session['time']}"
                s_dt = datetime.fromisoformat(s_str.replace('Z', '+00:00'))
                sessions_list.append({"name": name, "dt": s_dt})

        # Sort sessions chronologically
        sessions_list.sort(key=lambda x: x["dt"])

        target_session_dt = race_dt
        session_name = "Race"
        ongoing_session_name = None

        for i, s in enumerate(sessions_list):
            if s["dt"] > now:
                target_session_dt = s["dt"]
                session_name = s["name"]
                
                # Check if the previous session is still ongoing (assuming ~2 hours duration)
                if i > 0:
                    prev_s = sessions_list[i-1]
                    if (now - prev_s["dt"]).total_seconds() < 7200:
                        ongoing_session_name = prev_s["name"]
                break

        # 3. Open-Meteo Weather Integration
        lat = next_event["Circuit"]["Location"]["lat"]
        lon = next_event["Circuit"]["Location"]["long"]
        
        # We request current temperature and weather codes
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code&timezone=auto"
        weather_info = {"temp": "N/A", "condition": "Unknown"}
        
        try:
            w_res = requests.get(weather_url).json()
            weather_info = {
                "temp": f"{int(w_res['current']['temperature_2m'])}°C",
                # "weather_code": w_res['current']['weather_code'], 
                "condition": WMO_CODES.get(w_res['current']['weather_code'], "Unknown")# Use this to map icons in Flutter
            }
        except:
            pass

        # 4. Countdown Calculation
        delta = target_session_dt - now
        countdown = {
            "days": delta.days,
            "hours": delta.seconds // 3600,
            "minutes": (delta.seconds // 60) % 60,
            "seconds": delta.seconds % 60
        }

        if ongoing_session_name:
            next_session_str = f"Ongoing : {ongoing_session_name} | Next : {session_name}  Time Zone : UTC {target_session_dt.strftime('%Y-%m-%d %H:%M UTC')}"
        else:
            next_session_str = f"Session Name : {session_name}  Time Zone : UTC {target_session_dt.strftime('%Y-%m-%d %H:%M UTC')}"

        # 5. Country Flag Helper
        # We provide the ISO country code so Flutter can easily fetch a flag image
        country = next_event["Circuit"]["Location"]["country"]

        return {
            "race_name": next_event["raceName"],
            "circuit": next_event["Circuit"]["circuitName"],
            "flag_emoji": get_clean_flag(country),
            "weather": weather_info,
            "countdown": countdown,
            "next_session": next_session_str,
            "ongoing_session": ongoing_session_name,
            "is_sprint_weekend": "Sprint" in next_event or "SprintQualifying" in next_event
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Helper: Convert Country Name to ISO (Manual map for F1 specific names)
def get_clean_flag(country_name):
    # F1 countries often use shorthand, so we map them to ISO-2 codes first
    mapping = {
        "UK": "GB", "USA": "US", "UAE": "AE", "Netherlands": "NL", 
        "Saudi Arabia": "SA", "Italy": "IT", "Japan": "JP"
    }
    iso_code = mapping.get(country_name, country_name[:2].upper())
    
    try:
        # This library ensures the characters are paired correctly for modern UIs
        return flag.flag(iso_code) 
    except:
        return "🏁" # Fallback if code is invalid

@app.get("/drivers")
def get_drivers():
    try:
        response = requests.get(DRIVERS)
        response.raise_for_status()
        data = response.json()

        drivers_raw = data["MRData"]["DriverTable"]["Drivers"]

        clean_drivers = []
        for driver in drivers_raw:
            driver_entry = {
                "driverid": driver.get("driverId", "Unknown"),
                "firstname": driver.get("givenName", "Unknown"),
                "lastname": driver.get("familyName", "Unknown"),
                "nationality": driver.get("nationality", "Unknown"),
            }

            if "permanentNumber" in driver and driver["permanentNumber"]:
                driver_entry["number"] = driver["permanentNumber"]
            else:
                driver_entry["number"] = "TBA"

            if "code" in driver and driver["code"]:
                driver_entry["code"] = driver["code"]
            else:
                driver_entry["code"] = "---"

            clean_drivers.append(driver_entry)
        
        return {
            "season": data["MRData"]["DriverTable"]["season"],
            "total_drivers": len(clean_drivers), 
            "drivers": clean_drivers
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/constructors")
def get_constructors():
    response = requests.get(CONSTRUCTORS)
    response.raise_for_status()
    data = response.json()

    drivers_raw = data["MRData"]["ConstructorTable"]["Constructors"]

    clean_constructors = []
    for constructor in drivers_raw:
        constructor_entry = {
            "constructorid": constructor["constructorId"],
            "name": constructor["name"],
            "nationality": constructor["nationality"],
            "url": constructor["url"]
        }
        clean_constructors.append(constructor_entry)

    return {"season": data["MRData"]["ConstructorTable"]["season"],"total_constructors": len(clean_constructors), "constructors": clean_constructors}

@app.get("/constructor_standings")
def get_constructor_standings():
    try:
        response = requests.get(CONS_STANDINGS)
        response.raise_for_status()
        data = response.json()

        standings_lists = data["MRData"]["StandingsTable"]["StandingsLists"]

        # Check if the list is empty
        if not standings_lists:
            return {
                "season": data["MRData"]["StandingsTable"]["season"],
                "status": "SEASON IS YET TO BEGIN",
                "constructors": []
            }

        # If data exists, clean it
        standing_raw = standings_lists[0]["ConstructorStandings"]
        clean_constructors = []
        for item in standing_raw:
            cons_data = item.get("Constructor", {})
            clean_constructors.append({
                "position": item.get("position"),
                "points": item.get("points"),
                "name": cons_data.get("name", "Unknown"),
                "nationality": cons_data.get("nationality", "N/A")
            })

        return {
            "season": data["MRData"]["StandingsTable"]["season"],
            "status": "SEASON IN PROGRESS",
            "total_teams": len(clean_constructors), 
            "constructors": clean_constructors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"API Error: {str(e)}")

@app.get("/driver_standings")
def get_driver_standings():
    try:
        # Note: Ensure DRIVER_STANDINGS URL is used here, not CONS_STANDINGS
        response = requests.get(DRIVER_STANDINGS) 
        response.raise_for_status()
        data = response.json()

        standings_lists = data["MRData"]["StandingsTable"]["StandingsLists"]

        # Check if the list is empty
        if not standings_lists:
            return {
                "season": data["MRData"]["StandingsTable"]["season"],
                "status": "SEASON IS YET TO BEGIN",
                "drivers": []
            }

        # Access index [0] only after verifying it exists
        drivers_raw = standings_lists[0]["DriverStandings"]

        clean_drivers = []
        for item in drivers_raw:
            driver_data = item.get("Driver", {})
            clean_drivers.append({
                "position": item.get("position"),
                "points": item.get("points"),
                "driverid": driver_data.get("driverId"),
                "name": f"{driver_data.get('givenName')} {driver_data.get('familyName')}",
                "nationality": driver_data.get("nationality", "N/A"),
                "url": driver_data.get("url", "No URL")
            })

        return {
            "season": data["MRData"]["StandingsTable"]["season"],
            "status": "SEASON IN PROGRESS",
            "total_drivers": len(clean_drivers), 
            "drivers": clean_drivers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"API Error: {str(e)}")

@app.get("/circuits")
def get_circuits():
    try:
        response = requests.get(F1COMPNAION)
        response.raise_for_status()
        data = response.json()

        circuits_raw = data["MRData"]["RaceTable"]["Races"]

        clean_circuits = []
        for race in circuits_raw:
            country_name = race["Circuit"]["Location"]["country"]
            country_locality = race["Circuit"]["Location"]["locality"]
            layout_url = TRACK_LAYOUT.get(country_locality, "N/A")   
            circuit_entry = {
                "circuitid": race["Circuit"]["circuitId"],
                "circuitname": race["Circuit"]["circuitName"],
                "circuitlocation": country_locality,
                "circuitcountry": country_name,
                "circuitlayout": layout_url
            }
            clean_circuits.append(circuit_entry)

        return {
            "season": data["MRData"]["RaceTable"]["season"], 
            "circuits": len(clean_circuits), 
            "circuits": clean_circuits
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching F1 circuits: {str(e)}")


@app.get("/race_results/{round}/{year}")
def get_race_results(round: str, year: str):
    RESULTS = f"https://api.jolpi.ca/ergast/f1/{year}/{round}/results.json"
    try:
        response = requests.get(RESULTS)
        response.raise_for_status()
        data = response.json()

        races_raw = data["MRData"]["RaceTable"]["Races"]

        if not races_raw:
            return {
                "season": data["MRData"]["RaceTable"]["season"],
                "status": "RESULT NOT YET AVAILABLE","round":round,
            }

        race = races_raw[0]
        results_list = race.get("Results", [])

        clean_results = []
        for result in results_list:
            clean_results.append({
                "position": result["position"],
                "positionText": result["positionText"], # Useful for 'R' (Retired) or 'D' (Disqualified)
                "driver": f"{result['Driver']['givenName']} {result['Driver']['familyName']}",
                "constructor": result["Constructor"]["name"],
                "points": result["points"],
                "grid": result["grid"],
                "status": result["status"], # e.g., 'Finished', '+1 Lap', 'DNF'
                "time": result["Time"]["time"] if "Time" in result else "N/A",
                "fastest_lap_time": result.get("FastestLap", {}).get("Time", {}).get("time", "N/A")
            })

        return {
            "season": data["MRData"]["RaceTable"]["season"],
            "round": race["round"],
            "racename": race["raceName"],
            "results": clean_results
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching F1 races: {str(e)}")

import time
import concurrent.futures

# --- STATIC F1 CHAMPIONSHIP CACHES ---
# Hardcoded to prevent rate-limiting Jolpica with 150+ historical queries per startup
GLOBAL_WDC_MAP = {'michael_schumacher': 7, 'hamilton': 7, 'fangio': 5, 'prost': 4, 'vettel': 4, 'brabham': 3, 'stewart': 3, 'lauda': 3, 'piquet': 3, 'senna': 3, 'max_verstappen': 4, 'ascari': 2, 'clark': 2, 'hill': 2, 'emerson_fittipaldi': 2, 'hakkinen': 2, 'alonso': 2, 'farina': 1, 'hawthorn': 1, 'phil_hill': 1, 'surtees': 1, 'hulme': 1, 'rindt': 1, 'andretti': 1, 'scheckter': 1, 'jones': 1, 'keke_rosberg': 1, 'mansell': 1, 'damon_hill': 1, 'villeneuve': 1, 'raikkonen': 1, 'button': 1, 'nico_rosberg': 1}
GLOBAL_WCC_MAP = {'ferrari': 16, 'williams': 9, 'mclaren': 8, 'mercedes': 8, 'lotus': 7, 'red_bull': 6, 'cooper': 2, 'brabham': 2, 'renault': 2, 'vanwall': 1, 'brm': 1, 'matra': 1, 'tyrrell': 1, 'benetton': 1, 'brawn': 1}
GLOBAL_DRIVER_WCC_MAP = {'ferrari': 15, 'mclaren': 12, 'mercedes': 9, 'williams': 7, 'red_bull': 7, 'lotus': 6, 'brabham': 4, 'alfaromeo': 2, 'maserati': 2, 'cooper': 2, 'renault': 2, 'benetton': 2, 'tyrrell': 2, 'brm': 1, 'matra': 1, 'brawn': 1}
UPDATED_YEARS = set()

def update_dynamic_championships():
    current_year = datetime.now(timezone.utc).year
    for year in range(2025, current_year): # Only check 2025 onwards since 1950-2024 is static
        if year in UPDATED_YEARS: continue
        try:
            r1 = requests.get(f"https://api.jolpi.ca/ergast/f1/{year}/driverStandings.json")
            if r1.status_code == 200:
                st1 = r1.json()["MRData"]["StandingsTable"]["StandingsLists"]
                if st1:
                    d_id = st1[0]["DriverStandings"][0]["Driver"]["driverId"]
                    c_id = st1[0]["DriverStandings"][0]["Constructors"][0]["constructorId"]
                    GLOBAL_WDC_MAP[d_id] = GLOBAL_WDC_MAP.get(d_id, 0) + 1
                    GLOBAL_DRIVER_WCC_MAP[c_id] = GLOBAL_DRIVER_WCC_MAP.get(c_id, 0) + 1
                    
            r2 = requests.get(f"https://api.jolpi.ca/ergast/f1/{year}/constructorStandings.json")
            if r2.status_code == 200:
                st2 = r2.json()["MRData"]["StandingsTable"]["StandingsLists"]
                if st2:
                    c_id2 = st2[0]["ConstructorStandings"][0]["Constructor"]["constructorId"]
                    GLOBAL_WCC_MAP[c_id2] = GLOBAL_WCC_MAP.get(c_id2, 0) + 1
                    
            UPDATED_YEARS.add(year)
        except: pass

def ensure_champs_fetched():
    update_dynamic_championships()

@app.get("/constructor_stats")
def get_constructor_stats():
    ensure_champs_fetched()
    current_year = str(datetime.now(timezone.utc).year)
    
    try:
        current_res = requests.get("https://api.jolpi.ca/ergast/f1/current/constructors.json")
        current_res.raise_for_status()
        current_constructors = current_res.json()["MRData"]["ConstructorTable"]["Constructors"]

        current_standings_map = {}
        try:
            cs_res = requests.get("https://api.jolpi.ca/ergast/f1/current/constructorStandings.json")
            if cs_res.status_code == 200:
                cs_data = cs_res.json()["MRData"]["StandingsTable"]["StandingsLists"]
                if cs_data:
                    for standing in cs_data[0]["ConstructorStandings"]:
                        c_id = standing["Constructor"]["constructorId"]
                        current_standings_map[c_id] = {
                            "year": current_year,
                            "position": standing.get("position", "N/A"),
                            "points": standing.get("points", "0")
                        }
        except: pass

        # Baseline stats as provided by the user + estimated podiums for merged lineages up to 2025
        CONSTRUCTOR_BASE_STATS = {
            "ferrari": {"wcc": 16, "wdc": 15, "wins": 248, "entries": 1124, "podiums": 813},
            "mclaren": {"wcc": 10, "wdc": 12, "wins": 203, "entries": 995, "podiums": 522},
            "mercedes": {"wcc": 8, "wdc": 9, "wins": 134, "entries": 318, "podiums": 296},
            "red_bull": {"wcc": 6, "wdc": 7, "wins": 130, "entries": 383, "podiums": 281},
            "williams": {"wcc": 9, "wdc": 7, "wins": 114, "entries": 852, "podiums": 313},
            "alpine": {"wcc": 2, "wdc": 2, "wins": 35, "entries": 403, "podiums": 212},
            "aston_martin": {"wcc": 0, "wdc": 0, "wins": 1, "entries": 606, "podiums": 38},
            "haas": {"wcc": 0, "wdc": 0, "wins": 0, "entries": 182, "podiums": 0},
            "rb": {"wcc": 0, "wdc": 0, "wins": 2, "entries": 370, "podiums": 5},
            "audi": {"wcc": 0, "wdc": 0, "wins": 1, "entries": 614, "podiums": 27},
            "cadillac": {"wcc": 0, "wdc": 0, "wins": 0, "entries": 0, "podiums": 0}
        }

        # Dynamically fetch ONLY the current year's races and add them to the baseline!
        # This completely skips the need for massive pagination while perfectly merging lineages.
        current_year_races = []
        try:
            res = requests.get(f"https://api.jolpi.ca/ergast/f1/{current_year}/results.json?limit=1000")
            if res.status_code == 200:
                current_year_races = res.json()["MRData"]["RaceTable"]["Races"]
        except: pass

        current_year_stats = {}
        for race in current_year_races:
            participating = set()
            for result in race["Results"]:
                c_id = result["Constructor"]["constructorId"]
                participating.add(c_id)
                if c_id not in current_year_stats:
                    current_year_stats[c_id] = {"wins": 0, "podiums": 0, "entries": 0}
                    
                pos = result.get("position")
                if pos == "1": current_year_stats[c_id]["wins"] += 1
                if pos in ["1", "2", "3"]: current_year_stats[c_id]["podiums"] += 1
                
            for c_id in participating:
                current_year_stats[c_id]["entries"] += 1

        grid_stats = []
        for constructor in current_constructors:
            c_id = constructor["constructorId"]
            
            # Start with baseline (or 0 if somehow not mapped)
            base = CONSTRUCTOR_BASE_STATS.get(c_id, {"wcc": 0, "wdc": 0, "wins": 0, "entries": 0, "podiums": 0})
            
            # Add current year
            cy_stats = current_year_stats.get(c_id, {"wins": 0, "podiums": 0, "entries": 0})
            
            total_wins = base["wins"] + cy_stats["wins"]
            total_podiums = base["podiums"] + cy_stats["podiums"]
            total_entries = base["entries"] + cy_stats["entries"]
            
            win_rate = round((total_wins / total_entries * 100), 2) if total_entries > 0 else 0
            podium_rate = round((total_podiums / (total_entries * 2) * 100), 2) if total_entries > 0 else 0
            
            c_stats = current_standings_map.get(c_id, {"year": current_year, "position": "N/A", "points": "0"})
            
            grid_stats.append({
                "constructor_id": c_id,
                "constructor_name": constructor["name"],
                "stats": {
                    "constructor_championships": base["wcc"],
                    "driver_championships": base["wdc"],
                    "total_races": total_entries,
                    "wins": total_wins,
                    "win_percentage": f"{win_rate}%",
                    "podiums": total_podiums,
                    "podium_percentage": f"{podium_rate}%",
                    "current_season": c_stats
                }
            })
            
        return {
            "season": current_year,
            "total_constructors": len(grid_stats),
            "constructor_stats": grid_stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing stats: {str(e)}")


@app.get("/driver_stats")
def get_driver_stats():
    ensure_champs_fetched()
    current_year = str(datetime.now(timezone.utc).year)
    
    try:
        current_res = requests.get("https://api.jolpi.ca/ergast/f1/current/drivers.json")
        current_res.raise_for_status()
        current_drivers = current_res.json()["MRData"]["DriverTable"]["Drivers"]
        
        current_standings_map = {}
        try:
            cs_res = requests.get("https://api.jolpi.ca/ergast/f1/current/driverStandings.json")
            if cs_res.status_code == 200:
                cs_data = cs_res.json()["MRData"]["StandingsTable"]["StandingsLists"]
                if cs_data:
                    for standing in cs_data[0]["DriverStandings"]:
                        d_id = standing["Driver"]["driverId"]
                        current_standings_map[d_id] = {
                            "year": current_year,
                            "position": standing.get("position", "N/A"),
                            "points": standing.get("points", "0")
                        }
        except: pass

        DRIVER_BASE_STATS = {
            "albon": {"total_races": 132, "total_pole": 0, "total_wins": 0, "total_podiums": 2, "career_points": 308.0, "total_seasons": 6},
            "alonso": {"total_races": 428, "total_pole": 22, "total_wins": 32, "total_podiums": 106, "career_points": 2380.0, "total_seasons": 22},
            "antonelli": {"total_races": 24, "total_pole": 0, "total_wins": 0, "total_podiums": 3, "career_points": 135.0, "total_seasons": 1},
            "bearman": {"total_races": 27, "total_pole": 0, "total_wins": 0, "total_podiums": 0, "career_points": 46.0, "total_seasons": 2},
            "bortoleto": {"total_races": 24, "total_pole": 0, "total_wins": 0, "total_podiums": 0, "career_points": 19.0, "total_seasons": 1},
            "bottas": {"total_races": 247, "total_pole": 20, "total_wins": 10, "total_podiums": 67, "career_points": 1788.0, "total_seasons": 12},
            "colapinto": {"total_races": 27, "total_pole": 0, "total_wins": 0, "total_podiums": 0, "career_points": 5.0, "total_seasons": 2},
            "jak_crawford": {"total_races": 0, "total_pole": 0, "total_wins": 0, "total_podiums": 0, "career_points": 0.0, "total_seasons": 0},
            "gasly": {"total_races": 178, "total_pole": 0, "total_wins": 1, "total_podiums": 5, "career_points": 446.0, "total_seasons": 9},
            "hadjar": {"total_races": 24, "total_pole": 0, "total_wins": 0, "total_podiums": 1, "career_points": 50.0, "total_seasons": 1},
            "hamilton": {"total_races": 380, "total_pole": 104, "total_wins": 105, "total_podiums": 202, "career_points": 4955.5, "total_seasons": 19},
            "hulkenberg": {"total_races": 254, "total_pole": 1, "total_wins": 0, "total_podiums": 1, "career_points": 614.0, "total_seasons": 14},
            "lawson": {"total_races": 35, "total_pole": 0, "total_wins": 0, "total_podiums": 0, "career_points": 44.0, "total_seasons": 3},
            "leclerc": {"total_races": 173, "total_pole": 27, "total_wins": 8, "total_podiums": 50, "career_points": 1588.0, "total_seasons": 8},
            "arvid_lindblad": {"total_races": 0, "total_pole": 0, "total_wins": 0, "total_podiums": 0, "career_points": 0.0, "total_seasons": 0},
            "norris": {"total_races": 152, "total_pole": 16, "total_wins": 11, "total_podiums": 44, "career_points": 1344.0, "total_seasons": 7},
            "ocon": {"total_races": 180, "total_pole": 0, "total_wins": 1, "total_podiums": 4, "career_points": 474.0, "total_seasons": 9},
            "piastri": {"total_races": 70, "total_pole": 6, "total_wins": 9, "total_podiums": 26, "career_points": 728.0, "total_seasons": 3},
            "perez": {"total_races": 283, "total_pole": 3, "total_wins": 6, "total_podiums": 39, "career_points": 1585.0, "total_seasons": 14},
            "russell": {"total_races": 152, "total_pole": 8, "total_wins": 5, "total_podiums": 24, "career_points": 953.0, "total_seasons": 7},
            "sainz": {"total_races": 232, "total_pole": 6, "total_wins": 4, "total_podiums": 29, "career_points": 1257.5, "total_seasons": 11},
            "stroll": {"total_races": 191, "total_pole": 1, "total_wins": 0, "total_podiums": 3, "career_points": 315.0, "total_seasons": 9},
            "max_verstappen": {"total_races": 233, "total_pole": 48, "total_wins": 71, "total_podiums": 127, "career_points": 3301.5, "total_seasons": 11}
        }

        current_year_races = []
        try:
            res = requests.get(f"https://api.jolpi.ca/ergast/f1/{current_year}/results.json?limit=1000")
            if res.status_code == 200:
                current_year_races = res.json()["MRData"]["RaceTable"]["Races"]
        except: pass

        current_year_stats = {}
        for race in current_year_races:
            for result in race["Results"]:
                d_id = result["Driver"]["driverId"]
                if d_id not in current_year_stats:
                    current_year_stats[d_id] = {"races": 0, "wins": 0, "podiums": 0, "pole": 0, "points": 0.0}
                    
                current_year_stats[d_id]["races"] += 1
                current_year_stats[d_id]["points"] += float(result.get("points", 0.0))
                
                pos = result.get("position")
                if pos == "1": current_year_stats[d_id]["wins"] += 1
                if pos in ["1", "2", "3"]: current_year_stats[d_id]["podiums"] += 1
                if result.get("grid") == "1": current_year_stats[d_id]["pole"] += 1

        grid_stats = []
        for driver in current_drivers:
            d_id = driver["driverId"]
            base = DRIVER_BASE_STATS.get(d_id, {"total_races": 0, "total_pole": 0, "total_wins": 0, "total_podiums": 0, "career_points": 0.0, "total_seasons": 0})
            cy_stats = current_year_stats.get(d_id, {"races": 0, "wins": 0, "podiums": 0, "pole": 0, "points": 0.0})
            
            seasons_played = base["total_seasons"] + 1
            wdc_count = GLOBAL_WDC_MAP.get(d_id, 0)
            c_stats = current_standings_map.get(d_id, {"year": current_year, "position": "N/A", "points": "0"})

            grid_stats.append({
                "driver_id": d_id,
                "driver_name": f"{driver['givenName']} {driver['familyName']}",
                "career_stats": {
                    "world_championships": wdc_count,
                    "total_races": base["total_races"] + cy_stats["races"],
                    "total_pole": base["total_pole"] + cy_stats["pole"],
                    "total_wins": base["total_wins"] + cy_stats["wins"],
                    "total_podiums": base["total_podiums"] + cy_stats["podiums"],
                    "career_points": round(base["career_points"] + cy_stats["points"], 1),
                    "total_seasons": seasons_played,
                    "current_season": c_stats
                },
            })
            
        return {
            "season": current_year,
            "total_drivers": len(grid_stats),
            "driver_stats": grid_stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"API Error: {str(e)}")


@app.get("/news")
def get_f1_news():
    
    RSS_URL = "https://www.skysports.com/rss/12433"
    feed = feedparser.parse(RSS_URL)
    
    news_list = []
    try:
        for entry in feed.entries[:10]:
            image_url = ""
            
            # Check for standard RSS enclosures (common for images)
            if 'enclosures' in entry and len(entry.enclosures) > 0:
                image_url = entry.enclosures[0].get('url', '')
            
            # Fallback: Check for media:content tags (common in Sky/BBC feeds)
            elif 'media_content' in entry:
                image_url = entry.media_content[0].get('url', '')

            # Second Fallback: Regex search in summary/description if image is embedded in HTML
            elif not image_url and 'summary' in entry:
                img_match = re.search(r'<img [^>]*src="([^"]+)"', entry.summary)
                if img_match:
                    image_url = img_match.group(1)

            # --- CLEANING SUMMARY ---
            # Remove HTML tags from the summary so it's clean for your Flutter Text widget
            clean_summary = re.sub(r'<[^>]+>', '', entry.get('summary', ''))
            news_list.append({
                "title": entry.get('title', 'No Title'),
                "description": clean_summary[:150] + "...", # Short snippet
                "link": entry.get('link', ''),
                "published": entry.get('published', ''),
                "image": image_url if image_url else "https://raw.githubusercontent.com/JenilMacwan/f1companion-api/main/assets/track/f1_placeholder.webp"
            })
    
        return {
            "status": "ok",
            "source": "Sky Sports F1",
            "articles": news_list
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}    

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)
