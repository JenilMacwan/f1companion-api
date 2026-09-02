from fastapi import APIRouter, Query
from typing import Optional
from app.services.team_radio_service import get_team_radio_messages

router = APIRouter(
    prefix="/team-radio",
    tags=["Team Radio"]
)

@router.get("/latest")
def get_latest_team_radio(last_name: Optional[str] = Query(None, description="Filter by driver's last name (e.g., Verstappen, Norris)")):
    """
    Get the team radio communications from the latest or ongoing session.
    """
    return get_team_radio_messages(session_key="latest", last_name=last_name)
