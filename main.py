import uvicorn
import flag
import requests
import feedparser
import re
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, HTTPException
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
    "Bahrain": "https://github.com/JenilMacwan/f1companion-api/blob/997e3c439135be7d4fcf47fb050d66ce23e96921/assests/track/sakhir-bahrain2026.webp?raw=true",
    "Australia":"",
    "China":"",
    "Japan":"",
    "Canada":"",
    "Spain":"",
    "Austria":"",
    "UK":"",
    "Hungary":"",
    "Belgium":"",
    "Italy":"",
    "Azerbaijan":"",
    "USA":"",
    "Mexico":"",
    "Brazil":"",
    "Las Vegas":"",
    "Qatar":"",
    "Saudi Arabia":"",
    "Monaco":"",
    "USA":"",
    "Netherlands":"",
    "Singapore":"",
    "Qatar":"",
    "Saudi Arabia":"",
    "Monaco":"",
    "USA":"",
    "Netherlands":"",
    "Singapore":"",
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
            {"path": "/driver_stats/{driver_id}", "description": "Deep career stats for drivers"},
            {"path": "/constructor_stats/{constructor_id}", "description": "Team performance and history"},
            {"path": "/news", "description": "Latest F1 news"}
        ],
        "status": "online"
    }

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

        # 2. Earliest Session for Countdown
        # F1 weekends start with FP1. We find the earliest session provided by Jolpica.
        session_keys = ["FirstPractice", "SecondPractice", "ThirdPractice", "Qualifying", "Sprint", "SprintQualifying"]
        earliest_session_dt = race_dt # Default to race time if no sessions found
        
        for key in session_keys:
            session = next_event.get(key)
            if session:
                s_str = f"{session['date']}T{session['time']}"
                s_dt = datetime.fromisoformat(s_str.replace('Z', '+00:00'))
                if s_dt < earliest_session_dt:
                    earliest_session_dt = s_dt

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
        delta = earliest_session_dt - now
        countdown = {
            "days": delta.days,
            "hours": delta.seconds // 3600,
            "minutes": (delta.seconds // 60) % 60
        }

        # 5. Country Flag Helper
        # We provide the ISO country code so Flutter can easily fetch a flag image
        country = next_event["Circuit"]["Location"]["country"]

        return {
            "race_name": next_event["raceName"],
            "circuit": next_event["Circuit"]["circuitName"],
            "flag_emoji": get_clean_flag(country),
            "weather": weather_info,
            "countdown": countdown,
            "next_session": earliest_session_dt.strftime("%Y-%m-%d %H:%M UTC"),
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
                "driverid": driver["driverId"],
                "firstname": driver["givenName"],
                "lastname": driver["familyName"],
                "nationality": driver["nationality"],
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

@app.get("/constructorstandings")
def get_constructorstandings():
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

@app.get("/driverstandings")
def get_driverstandings():
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
            layout_url = TRACK_LAYOUT.get(country_name, "N/A")   
            circuit_entry = {
                "circuitid": race["Circuit"]["circuitId"],
                "circuitname": race["Circuit"]["circuitName"],
                "circuitlocation": race["Circuit"]["Location"]["locality"],
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

@app.get("/constructor_stats/{constructor_id}")
def get_constructor_stats(constructor_id: str):
    team_wins = 0
    team_podiums = 0
    total_gp_entries = 0 # Count of unique race weekends entered
    
    offset = 0
    limit = 100 
    
    try:
        # --- 1. FETCH ALL TEAM RACE RESULTS (Pagination) ---
        while True:
            # RESULTS_URL fetches every race the team has ever entered
            RESULTS_URL = f"https://api.jolpi.ca/ergast/f1/constructors/{constructor_id}/results.json?limit={limit}&offset={offset}"
            response = requests.get(RESULTS_URL)
            response.raise_for_status()
            data = response.json()
            
            races = data["MRData"]["RaceTable"]["Races"]
            if not races:
                break
                
            for race in races:
                # Increment per unique Grand Prix (not per car)
                total_gp_entries += 1 
                
                # Check results for both cars entered by the team
                for result in race["Results"]:
                    position = result.get("position")
                    
                    if position == "1":
                        team_wins += 1
                    if position in ["1", "2", "3"]:
                        team_podiums += 1
                        
            offset += limit

        # --- 2. CALCULATE PERCENTAGES ---
        # Win % based on one trophy available per race
        win_rate = round((team_wins / total_gp_entries * 100), 2) if total_gp_entries > 0 else 0
        
        # Podium % based on two cars per team (two chances for a podium per race)
        podium_rate = round((team_podiums / (total_gp_entries * 2) * 100), 2) if total_gp_entries > 0 else 0

        # --- 3. RETURN CLEANED DATA ---
        return {
            "constructor_id": constructor_id,
            "stats": {
                "total_races": total_gp_entries,
                "wins": team_wins,
                "win_percentage": f"{win_rate}%",
                "podiums": team_podiums,
                "podium_percentage": f"{podium_rate}%"
            }
        }
        
    except Exception as e:
        # Generic error handling to prevent API crashes
        raise HTTPException(status_code=500, detail=f"Error processing stats: {str(e)}")

@app.get("/driver_stats/{driver_id}")
def get_driver_stats(driver_id: str):
    career_wins = 0
    career_podiums = 0
    total_points = 0.0
    career_pole = 0
    active_seasons = set()
    
    # This list will hold EVERY race, bypassing the 100 limit
    career_history = [] 
    
    offset = 0
    limit = 100 # We must play by Jolpica's 100-item rule
    
    try:
        while True:
            # The 'offset' moves forward by 100 every time the loop runs
            RESULTS_URL = f"https://api.jolpi.ca/ergast/f1/drivers/{driver_id}/results.json?limit={limit}&offset={offset}"
            
            response = requests.get(RESULTS_URL)
            response.raise_for_status()
            data = response.json()
            
            races = data["MRData"]["RaceTable"]["Races"]
            
            # If the list is empty, we have successfully downloaded the entire career!
            if not races:
                break
                
            for race in races:
                active_seasons.add(race["season"])
                result = race["Results"][0]
                
                points_scored = float(result.get("points", 0.0))
                total_points += points_scored
                
                position = result.get("position")
                if position == "1":
                    career_wins += 1
                if position in ["1", "2", "3"]:
                    career_podiums += 1
                
                pole = result.get("grid")
                if pole == "1":
                    career_pole += 1
                    
                # Add this race to our massive master list
                career_history.append({
                    "season": race["season"],
                    "round": race["round"],
                    "race_name": race["raceName"],
                    "constructor": result["Constructor"]["name"],
                    "grid": result["grid"],
                    "finish_position": position,
                    "points": points_scored
                })
                
            # Move the offset forward to grab the next "page" of 100 races
            offset += limit
            
        if not career_history:
            return {"error": "No career data found for this driver."}
            
        # --- 2. FETCH WORLD CHAMPIONSHIPS (WDC) ---
        wdc_count = 0
        
        # Since Jolpica demands a year, we loop through the years they actually raced!
        for year in active_seasons:
            # Crucial: Skip the current unfinished season so we don't accidentally 
            # crown someone a World Champion just because they won Round 1!
            if year == "2026": 
                continue
                
            try:
                # Ask the API for their specific standing in that specific year
                WDC_URL = f"https://api.jolpi.ca/ergast/f1/{year}/drivers/{driver_id}/driverstandings.json"
                wdc_response = requests.get(WDC_URL)
                
                if wdc_response.status_code == 200:
                    wdc_data = wdc_response.json()
                    standings_list = wdc_data["MRData"]["StandingsTable"]["StandingsLists"]
                    
                    # If data exists and their position is "1", add a Championship!
                    if standings_list:
                        standing = standings_list[0]["DriverStandings"][0]
                        if standing.get("position") == "1":
                            wdc_count += 1
                            
            except Exception as e:
                print(f"Warning - WDC Fetch Error for {year}: {e}")
                wdc_count = "N/A"

        return {
            "driver_id": driver_id,
            "driver_name": f"{result['Driver']['givenName']} {result['Driver']['familyName']}",
            "career_stats": {
                "world_championships": wdc_count,
                "total_races": len(career_history),
                "total_pole": career_pole,
                "total_wins": career_wins,
                "total_podiums": career_podiums,
                "career_points": round(total_points, 1),
                "total_seasons": len(active_seasons)
            },
            "history": career_history 
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
