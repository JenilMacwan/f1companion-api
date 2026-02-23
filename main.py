import requests
from datetime import datetime
from fastapi import FastAPI, HTTPException

app = FastAPI()

F1COMPNAION = "https://api.jolpi.ca/ergast/f1/2026.json"



DRIVER_STANDINGS = "https://api.jolpi.ca/ergast/f1/2026/driverstandings.json"
CONS_STANDINGS = "https://api.jolpi.ca/ergast/f1/2026/constructorstandings.json"

DRIVERS = "https://api.jolpi.ca/ergast/f1/2026/drivers.json"
CONSTRUCTORS = "https://api.jolpi.ca/ergast/f1/2026/constructors.json"

@app.get("/")
def read_root():
    return {"message": "Welcome to the F1 Companion API"}

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

@app.get("/next_race")
def get_next_race():
    response = requests.get(F1COMPNAION)
    response.raise_for_status()
    data = response.json()

    today = datetime.now().date()
    current_time = datetime.now().time()

    for race in data["MRData"]["RaceTable"]["Races"]:
        race_date = datetime.strptime(race["date"], "%Y-%m-%d").date()
        if race_date >= today:
            return {
                "status": "Live" if (race_date == today and race_time == current_time) 
                else "Upcoming" if race_date > today 
                else "Past",
                "race_name": race["raceName"],
                "circuit_name": race["Circuit"]["circuitName"],
                "circuit_location": race["Circuit"]["Location"]["locality"],
                "circuit_country": race["Circuit"]["Location"]["country"],
                "race_date": race["date"],
                "race_time": race["time"],
                "days_until": (race_date - today).days
            }

    return {"message": "No upcoming races found"}

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

    return {"season": data["MRData"]["ConstructorTable"]["season"],"constructors": len(clean_constructors), "constructors": clean_constructors}

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
            circuit_entry = {
                "circuitid": race["Circuit"]["circuitId"],
                "circuitname": race["Circuit"]["circuitName"],
                "circuitlocation": race["Circuit"]["Location"]["locality"],
                "circuitcountry": race["Circuit"]["Location"]["country"],
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
    career_wins = 0
    career_podiums = 0
    # career_wdc = 0
    # career_wcc = 0
    active_seasons = set()
    
    # This list will hold EVERY race, bypassing the 100 limit
    career_history = [] 
    
    offset = 0
    limit = 100 # We must play by Jolpica's 100-item rule
    
    try:
        while True:
            # The 'offset' moves forward by 100 every time the loop runs
            RESULTS_URL = f"https://api.jolpi.ca/ergast/f1/constructors/{constructor_id}/results.json?limit={limit}&offset={offset}"
            
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
                
                position = result.get("position")
                if position == "1":
                    career_wins += 1
                if position in ["1", "2", "3"]:
                    career_podiums += 1
                
                # Add the full race result to our history list
                career_history.append({
                    "season": race["season"],
                    "round": race["round"],
                    "raceName": race["raceName"],
                    "position": position,
                    "status": result["status"],
                    "points": result["points"]
                })
            
            # Move to the next page of results
            offset += limit
            
        if not career_history:
            return {"error": "No career data found for this driver."}    

        # Calculate the first and last season
        first_season = min(active_seasons)
        last_season = max(active_seasons)
        
        # Calculate win percentage
        total_races_entered = len(career_history)
        win_percentage = (career_wins / total_races_entered * 100) if total_races_entered > 0 else 0.0
        
        # Calculate podium percentage
        podium_percentage = (career_podiums / total_races_entered * 100) if total_races_entered > 0 else 0.0



        return {
            "constructorId": constructor_id,
            "name": data["MRData"]["RaceTable"]["constructorId"],
            "career_wins": career_wins,
            "career_podiums": career_podiums,
            "first_season": first_season,
            "last_season": last_season,
            "total_seasons": len(active_seasons),
            "win_percentage": round(win_percentage, 2),
            "career_history": career_history
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching F1 races: {str(e)}")

# @app.get("/constructor_stats/{constructor_id}")
# def get_constructor_stats(constructor_id: str):
#     team_wins = 0
#     team_podiums = 0
#     total_points = 0.0
#     active_seasons = set()
    
#     # NEW: We must track total unique races entered to calculate percentages
#     team_races = 0 
    
#     offset = 0
#     limit = 100 
    
#     try:
#         # --- 1. FETCH ALL TEAM RACE RESULTS (Pagination) ---
#         while True:
#             RESULTS_URL = f"https://api.jolpi.ca/ergast/f1/constructors/{constructor_id}/results.json?limit={limit}&offset={offset}"
            
#             response = requests.get(RESULTS_URL)
#             response.raise_for_status()
#             data = response.json()
            
#             races = data["MRData"]["RaceTable"]["Races"]
            
#             if not races:
#                 break
                
#             for race in races:
#                 active_seasons.add(race["season"])
#                 team_races += 1 # Count every unique race weekend the team entered
                
#                 for result in race["Results"]:
#                     points_scored = float(result.get("points", 0.0))
#                     total_points += points_scored
                    
#                     position = result.get("position")
#                     if position == "1":
#                         team_wins += 1
#                     if position in ["1", "2", "3"]:
#                         team_podiums += 1
                        
#             offset += limit

#         # --- 2. FETCH WCC and WDC (The Bulletproof "Global Check" Method) ---
#         wcc_count = 0
#         wdc_count = 0
        
#         for year in active_seasons:
#             if year == "2026": # Skip the ongoing season!
#                 continue
                
#             try:
#                 # 2A. Global WCC Check (limit=1 only grabs the 1st place team)
#                 WCC_URL = f"https://api.jolpi.ca/ergast/f1/{year}/constructorstandings.json?limit=1"
#                 wcc_resp = requests.get(WCC_URL)
                
#                 if wcc_resp.status_code == 200:
#                     c_data = wcc_resp.json()["MRData"]["StandingsTable"]["StandingsLists"]
#                     # WCC didn't exist before 1958, so checking 'if c_data' safely skips earlier years
#                     if c_data: 
#                         champ_constructor = c_data[0]["ConstructorStandings"][0]["Constructor"]["constructorId"]
#                         if champ_constructor == constructor_id:
#                             wcc_count += 1

#                 # 2B. Global WDC Check (limit=1 only grabs the 1st place driver)
#                 WDC_URL = f"https://api.jolpi.ca/ergast/f1/{year}/driverstandings.json?limit=1"
#                 wdc_resp = requests.get(WDC_URL)
                
#                 if wdc_resp.status_code == 200:
#                     d_data = wdc_resp.json()["MRData"]["StandingsTable"]["StandingsLists"]
#                     if d_data:
#                         # Drivers sometimes drove for multiple teams in a single historic year (e.g., Fangio). 
#                         # We check the champion's entire constructor list.
#                         champ_constructors = d_data[0]["DriverStandings"][0]["Constructors"]
#                         for c in champ_constructors:
#                             if c["constructorId"] == constructor_id:
#                                 wdc_count += 1
#                                 break
                                
#             except Exception as e:
#                 print(f"Warning - Championship Fetch Error for {year}: {e}")

#         # --- 3. CALCULATE PERCENTAGES ---
#         win_percentage = round((team_wins / team_races) * 100, 2) if team_races > 0 else 0.0
#         podium_percentage = round((team_podiums / team_races) * 100, 2) if team_races > 0 else 0.0

#         # --- 4. RETURN THE FULL PACKAGE ---
#         return {
#             "constructor_id": constructor_id,
#             "career_stats": {
#                 "WCC": wcc_count,
#                 "WDC": wdc_count,
#                 "total_races": team_races,
#                 "total_wins": team_wins,
#                 "win_percentage": f"{win_percentage}%",
#                 "total_podiums": team_podiums,
#                 "podium_percentage": f"{podium_percentage}%",
#                 "total_points": round(total_points, 1),
#                 "total_seasons": len(active_seasons)
#             }
#         }
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"API Error: {str(e)}")
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)
