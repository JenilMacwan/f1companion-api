from fastapi import APIRouter, HTTPException
from typing import Optional
from app.services.live_timing_service import live_timing_state, state_lock
import threading
import time
import random

_mock_active = False
_mock_thread = None

def mock_data_updater():
    global _mock_active
    while _mock_active:
        time.sleep(1.0)
        with state_lock:
            # Simulate changing weather
            weather = live_timing_state.get("WeatherData", {})
            if weather and "TrackTemp" in weather:
                try:
                    temp = float(weather["TrackTemp"])
                    weather["TrackTemp"] = f"{temp + random.uniform(-0.2, 0.2):.1f}"
                    
                    air_temp = float(weather.get("AirTemp", "25.0"))
                    weather["AirTemp"] = f"{air_temp + random.uniform(-0.1, 0.1):.1f}"
                except:
                    pass
            
            # Re-inject these so the real live F1 stream doesn't immediately overwrite our test values
            live_timing_state["SessionInfo"] = {"Type": "Qualifying"}
            
            clock = live_timing_state.get("ExtrapolatedClock", {})
            if clock and "Remaining" in clock:
                # Mock a ticking clock
                try:
                    h, m, s = map(int, clock["Remaining"].split(":"))
                    total_seconds = h * 3600 + m * 60 + s
                    if total_seconds > 0:
                        total_seconds -= 1
                    clock["Remaining"] = f"{total_seconds//3600:02d}:{(total_seconds%3600)//60:02d}:{total_seconds%60:02d}"
                except:
                    live_timing_state["ExtrapolatedClock"] = {"Remaining": "00:45:12", "Extrapolating": True}
            else:
                live_timing_state["ExtrapolatedClock"] = {"Remaining": "00:45:12", "Extrapolating": True}

            timing = live_timing_state.get("TimingData", {})
            if "SessionPart" not in timing:
                timing["SessionPart"] = 2
            
            lines = timing.get("Lines", {})
            if not lines:
                continue
                
            # Simulate Lando Norris closing/dropping gap
            norris = lines.get("4", {})
            if norris and "TimeDiffToFastest" in norris:
                try:
                    gap_str = norris["TimeDiffToFastest"].replace("+", "")
                    if gap_str:
                        gap = float(gap_str)
                        new_gap = max(0.1, gap + random.uniform(-0.150, 0.100)) # Tend to close the gap slightly
                        norris["TimeDiffToFastest"] = f"+{new_gap:.3f}"
                        norris["TimeDiffToPositionAhead"] = f"+{new_gap:.3f}"
                        
                        # Simulate sector time updates
                        if random.random() > 0.5:
                            s1 = float(norris["Sectors"]["0"]["Value"]) + random.uniform(-0.05, 0.05)
                            norris["Sectors"]["0"]["Value"] = f"{s1:.3f}"
                            # Randomly flash purple/green
                            if random.random() > 0.8:
                                norris["Sectors"]["0"]["OverallFastest"] = not norris["Sectors"]["0"].get("OverallFastest", False)
                except ValueError:
                    pass

            # Simulate Verstappen updating his lap time and incrementing lap
            verstappen = lines.get("1", {})
            if verstappen and random.random() > 0.7:
                verstappen["LastLapTime"]["Value"] = f"1:24.{random.randint(100, 999)}"
                if random.random() > 0.5:
                    current_laps = verstappen.get("NumberOfLaps", 45)
                    verstappen["NumberOfLaps"] = current_laps + 1
                
            # Simulate Leclerc entering/exiting pits
            leclerc = lines.get("16", {})
            if leclerc and random.random() > 0.85:
                leclerc["InPit"] = not leclerc.get("InPit", True)


router = APIRouter(
    prefix="/live-timing",
    tags=["Live Timing"]
)

@router.get("")
def get_all_live_timing():
    """
    Returns the full raw in-memory live timing state for all drivers.
    """
    with state_lock:
        return live_timing_state

@router.get("/test-mode")
def enable_test_mode():
    """
    Injects mock live timing data into the in-memory state for testing the UI.
    """
    global _mock_active, _mock_thread
    
    with state_lock:
        live_timing_state["TrackStatus"] = {"Message": "GreenFlag"}
        live_timing_state["WeatherData"] = {"AirTemp": "25.0", "TrackTemp": "40.0"}
        live_timing_state["ExtrapolatedClock"] = {"Remaining": "00:45:12", "Extrapolating": True}
        live_timing_state["SessionInfo"] = {"Type": "Qualifying"}
        live_timing_state["RaceControlMessages"] = [
            {"Utc": "2026-09-25T08:30:00Z", "Category": "Other", "Message": "SESSION START"},
            {"Utc": "2026-09-25T08:41:41Z", "Category": "SafetyCar", "Message": "VSC DEPLOYED"},
            {"Utc": "2026-09-25T08:41:46Z", "Category": "Flag", "Message": "DOUBLE YELLOW IN TRACK SECTOR 19"}
        ]
        
        live_timing_state["DriverList"] = {
            "1": {"RacingNumber": "1", "BroadcastName": "M VERSTAPPEN", "TeamName": "Red Bull Racing", "TeamColour": "3671C6"},
            "4": {"RacingNumber": "4", "BroadcastName": "L NORRIS", "TeamName": "McLaren", "TeamColour": "FF8000"},
            "44": {"RacingNumber": "44", "BroadcastName": "L HAMILTON", "TeamName": "Mercedes", "TeamColour": "27F4D2"},
            "16": {"RacingNumber": "16", "BroadcastName": "C LECLERC", "TeamName": "Ferrari", "TeamColour": "E80020"}
        }
        
        live_timing_state["TimingData"] = {
            "SessionPart": 2,
            "Lines": {
                "1": {
                    "Position": "1", "NumberOfLaps": 45, "TimeDiffToFastest": "", "TimeDiffToPositionAhead": "",
                    "LastLapTime": {"Value": "1:24.321", "OverallFastest": True, "PersonalFastest": True},
                    "Sectors": {"0": {"Value": "28.123", "PersonalFastest": True}, "1": {"Value": "29.456", "OverallFastest": True}, "2": {"Value": "26.742", "PersonalFastest": True}},
                    "Speeds": {"ST": {"Value": "332"}, "FL": {"Value": "295"}, "I1": {"Value": "270"}, "I2": {"Value": "280"}},
                    "InPit": False, "Stopped": False, "Retired": False
                },
                "4": {
                    "Position": "2", "NumberOfLaps": 45, "TimeDiffToFastest": "+1.234", "TimeDiffToPositionAhead": "+1.234",
                    "LastLapTime": {"Value": "1:24.500", "OverallFastest": False, "PersonalFastest": True},
                    "Sectors": {"0": {"Value": "28.200"}, "1": {"Value": "29.500"}, "2": {"Value": "26.800"}},
                    "Speeds": {"ST": {"Value": "328"}, "FL": {"Value": "291"}, "I1": {"Value": "268"}, "I2": {"Value": "278"}},
                    "InPit": False, "Stopped": False, "Retired": False
                },
                "44": {
                    "Position": "3", "NumberOfLaps": 45, "TimeDiffToFastest": "+5.678", "TimeDiffToPositionAhead": "+4.444",
                    "LastLapTime": {"Value": "1:25.100", "OverallFastest": False, "PersonalFastest": False},
                    "Sectors": {"0": {"Value": "28.400"}, "1": {"Value": "29.700"}, "2": {"Value": "27.000"}},
                    "InPit": False, "Stopped": False, "Retired": False
                },
                "16": {
                    "Position": "4", "NumberOfLaps": 44, "TimeDiffToFastest": "+12.000", "TimeDiffToPositionAhead": "+6.322",
                    "LastLapTime": {"Value": "1:35.000"},
                    "Sectors": {"0": {"Value": "31.200"}, "1": {"Value": "33.500"}, "2": {"Value": "30.800"}},
                    "InPit": True, "Stopped": False, "Retired": False
                }
            }
        }
        
        live_timing_state["TimingAppData"] = {
            "Lines": {
                "1": {"Stints": {"1": {"Compound": "SOFT", "TotalLaps": 10}}},
                "4": {"Stints": {"1": {"Compound": "MEDIUM", "TotalLaps": 15}}},
                "44": {"Stints": {"1": {"Compound": "HARD", "TotalLaps": 25}}},
                "16": {"Stints": {"1": {"Compound": "INTERMEDIATE", "TotalLaps": 5}}}
            }
        }
        
        live_timing_state["TimingStats"] = {
            "Lines": {
                "1": {
                    "PersonalBestLapTime": {"Value": "1:24.321"},
                    "PersonalBestSectors": [{"Value": "28.123"}, {"Value": "29.456"}, {"Value": "26.742"}]
                },
                "4": {
                    "PersonalBestLapTime": {"Value": "1:24.500"},
                    "PersonalBestSectors": [{"Value": "28.200"}, {"Value": "29.500"}, {"Value": "26.800"}]
                }
            }
        }
        
    if not _mock_active:
        _mock_active = True
        _mock_thread = threading.Thread(target=mock_data_updater, daemon=True)
        _mock_thread.start()
        
    return {"message": "Test mode activated. Mock data injected and simulating live updates."}

@router.get("/{racing_number}")
def get_driver_live_timing(racing_number: str):
    """
    Returns the live timing state filtered for a specific driver.
    """
    with state_lock:
        # Extract raw data to parse
        driver_info = {}
        if "DriverList" in live_timing_state and racing_number in live_timing_state["DriverList"]:
            driver_info = live_timing_state["DriverList"][racing_number]
            
        timing_data = {}
        if "TimingData" in live_timing_state and "Lines" in live_timing_state["TimingData"]:
            timing_data = live_timing_state["TimingData"]["Lines"].get(racing_number, {})

        timing_stats = {}
        if "TimingStats" in live_timing_state and "Lines" in live_timing_state["TimingStats"]:
            timing_stats = live_timing_state["TimingStats"]["Lines"].get(racing_number, {})

        timing_app_data = {}
        if "TimingAppData" in live_timing_state and "Lines" in live_timing_state["TimingAppData"]:
            timing_app_data = live_timing_state["TimingAppData"]["Lines"].get(racing_number, {})

        if not driver_info and not timing_data:
            raise HTTPException(status_code=404, detail=f"No live timing data found for driver {racing_number}")

        # Parse and Clean up Data
        current_tyre = "UNKNOWN"
        tyre_age = 0
        stints = timing_app_data.get("Stints", [])
        if stints:
            last_stint = stints[-1]
            current_tyre = last_stint.get("Compound", "UNKNOWN")
            # Calculate laps on this tyre (TotalLaps in stint or calculate from StartLaps)
            total_laps_stint = last_stint.get("TotalLaps", 0)
            start_laps = last_stint.get("StartLaps", 0)
            tyre_age = total_laps_stint - start_laps if total_laps_stint >= start_laps else total_laps_stint

        sectors = timing_data.get("Sectors", [])
        
        cleaned_data = {
            "driver": {
                "racing_number": driver_info.get("RacingNumber", racing_number),
                "broadcast_name": driver_info.get("BroadcastName", ""),
                "full_name": driver_info.get("FullName", ""),
                "team_name": driver_info.get("TeamName", ""),
                "team_colour": f"#{driver_info.get('TeamColour', 'FFFFFF')}",
                "headshot_url": driver_info.get("HeadshotUrl", "")
            },
            "position": timing_data.get("Position", ""),
            "status": {
                "in_pit": timing_data.get("InPit", False),
                "pit_out": timing_data.get("PitOut", False),
                "retired": timing_data.get("Retired", False),
                "stopped": timing_data.get("Stopped", False)
            },
            "race_stats": {
                "laps_completed": timing_data.get("NumberOfLaps", 0),
                "pit_stops": timing_data.get("NumberOfPitStops", 0)
            },
            "gaps": {
                "to_leader": timing_data.get("TimeDiffToFastest", ""),
                "to_ahead": timing_data.get("TimeDiffToPositionAhead", "")
            },
            "lap_times": {
                "last_lap": timing_data.get("LastLapTime", {}).get("Value", ""),
                "best_lap": timing_data.get("BestLapTime", {}).get("Value", ""),
                "personal_best": timing_stats.get("PersonalBestLapTime", {}).get("Value", "")
            },
            "current_sectors": {
                "sector_1": {
                    "value": sectors[0].get("Value", "") if len(sectors) > 0 else "",
                    "personal_fastest": sectors[0].get("PersonalFastest", False) if len(sectors) > 0 else False,
                    "overall_fastest": sectors[0].get("OverallFastest", False) if len(sectors) > 0 else False
                },
                "sector_2": {
                    "value": sectors[1].get("Value", "") if len(sectors) > 1 else "",
                    "personal_fastest": sectors[1].get("PersonalFastest", False) if len(sectors) > 1 else False,
                    "overall_fastest": sectors[1].get("OverallFastest", False) if len(sectors) > 1 else False
                },
                "sector_3": {
                    "value": sectors[2].get("Value", "") if len(sectors) > 2 else "",
                    "personal_fastest": sectors[2].get("PersonalFastest", False) if len(sectors) > 2 else False,
                    "overall_fastest": sectors[2].get("OverallFastest", False) if len(sectors) > 2 else False
                }
            },
            "speeds": {
                "st": timing_data.get("Speeds", {}).get("ST", {}).get("Value", ""),
                "i1": timing_data.get("Speeds", {}).get("I1", {}).get("Value", ""),
                "i2": timing_data.get("Speeds", {}).get("I2", {}).get("Value", ""),
                "fl": timing_data.get("Speeds", {}).get("FL", {}).get("Value", "")
            },
            "tyre": {
                "compound": current_tyre,
                "age_laps": tyre_age,
                "all_stints": [
                    {
                        "compound": stint.get("Compound", "UNKNOWN"),
                        "new": stint.get("New", "false") == "true",
                        "laps_on_tyre": stint.get("TotalLaps", 0),
                        "started_on_lap": stint.get("StartLaps", 0)
                    }
                    for stint in stints
                ]
            },
            "race_control_messages": [
                msg for msg in live_timing_state.get("RaceControlMessages", [])
                if isinstance(msg, dict) and (msg.get("Category") == "Flag" or "session" in msg.get("Message", "").lower())
            ]
        }
            
        return cleaned_data
