"""
Background monitor to prevent the host (like Render) from sleeping due to inactivity.
"""

import asyncio
import os
from app.core.http_client import http_client

async def start_keep_alive(interval_minutes: int = 14):
    """
    Pings the application's own /health endpoint to prevent it from going to sleep.
    Render free tier sleeps after 15 minutes of inactivity.
    """
    interval_seconds = interval_minutes * 60
    # Use environment variable if set by Render, otherwise fallback to the known URL
    app_url = os.getenv("RENDER_EXTERNAL_URL", "https://f1-companion-api-ba5k.onrender.com")
    health_url = f"{app_url.rstrip('/')}/health"
    
    print(f"Starting keep-alive monitor. Pinging {health_url} every {interval_minutes} minutes...")
    
    # Wait initially before first ping so the server fully starts
    await asyncio.sleep(60)
    
    while True:
        try:
            # We use asyncio.to_thread to prevent blocking the async event loop with a synchronous network request
            response = await asyncio.to_thread(http_client.session.get, health_url, timeout=10.0)
            if response.status_code == 200:
                print("Keep-alive ping successful.")
            else:
                print(f"Keep-alive ping failed with status: {response.status_code}")
        except Exception as e:
            print(f"Error during keep-alive ping: {e}")
            
        await asyncio.sleep(interval_seconds)
