"""
WebSocket connection manager for real-time race control updates.
"""

from typing import List, Dict, Any
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_json(self, data: Dict[str, Any]):
        """Send JSON data to all active connections."""
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                # If a connection is dead, remove it
                print(f"Error broadcasting to a websocket, removing connection: {e}")
                self.disconnect(connection)

# Global singleton manager instance
websocket_manager = ConnectionManager()
