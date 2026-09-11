from fastapi import APIRouter, HTTPException
from typing import Optional
from app.services.live_timing_service import live_timing_state, state_lock

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
            }
        }
            
        return cleaned_data
