"""
Race Control router.

Endpoint: /race_control
"""

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
import requests
import json

from app.services.race_control_service import get_race_control_messages
from app.core.websocket_manager import websocket_manager

router = APIRouter()

@router.get("/race_control")
def race_control(session_key: str = Query("latest", description="The session key (e.g., 'latest' or '9158')")):
    try:
        return get_race_control_messages(session_key=session_key)
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching race control messages: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing race control messages: {str(e)}"
        )

@router.websocket("/ws/race_control")
async def websocket_race_control(websocket: WebSocket):
    """
    WebSocket endpoint for real-time race control updates.
    """
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep the connection open.
            # Clients shouldn't need to send data, but we can listen for pings or disconnects.
            data = await websocket.receive_text()
            # Can process incoming messages from the client here if needed
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
        print("Client disconnected from race control live stream.")
