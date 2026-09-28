import json
import logging
import threading
import time
from fastf1.livetiming.client import SignalRClient
from signalrcore.messages.completion_message import CompletionMessage

logger = logging.getLogger("InMemoryLiveTiming")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# In-memory store for the latest live timing data
live_timing_state = {
    "TimingData": {},
    "TimingStats": {},
    "TimingAppData": {},
    "DriverList": {},
    "TrackStatus": {},
    "WeatherData": {},
    "SessionInfo": {},
    "RaceControlMessages": []
}

# We use a lock to ensure thread-safe updates to the dictionary
state_lock = threading.Lock()

class InMemorySignalRClient(SignalRClient):
    def __init__(self, timeout=60, logger=None):
        # We pass a dummy filename since we'll override file writing
        super().__init__("dummy.txt", filemode='w', timeout=timeout, logger=logger)
        
    def _run(self):
        # Override _run to not open a file
        from fastf1.internals.f1auth import get_auth_token
        import requests
        from signalrcore.hub_connection_builder import HubConnectionBuilder
        
        # Pre-negotiate to the get a valid AWSALBCORS header token
        r = requests.options(self._negotiate_url, headers=self.headers)
        self.headers.update(
            {"Cookie": f"AWSALBCORS={r.cookies['AWSALBCORS']}"}
        )

        def custom_auth_token():
            import os
            token = os.getenv("F1_AUTH_TOKEN")
            if token:
                return token.strip()
            from fastf1.internals.f1auth import get_auth_token
            return get_auth_token()

        # Configure and create connection
        options = {
            "verify_ssl": True,
            "access_token_factory": None if self._no_auth else custom_auth_token,
            "headers": self.headers
        }

        self._connection = HubConnectionBuilder() \
            .with_url(self._connection_url, options=options) \
            .configure_logging(logging.INFO) \
            .build()

        self._connection.on_open(self._on_connect)
        self._connection.on_close(self._on_close)
        self._connection.on('feed', self._on_message)

        self._connection.start()

        # wait for connection to be established
        while not self._is_connected:
            time.sleep(0.1)

        self._connection.send(
            "Subscribe", [self.topics], on_invocation=self._on_message
        )

    def _exit(self):
        self._connection.stop()
        # No file to close

    def _on_message(self, msg):
        self._t_last_message = time.time()
        
        if isinstance(msg, CompletionMessage):
            # This is the initial sync
            for key, val in msg.result.items():
                self._update_state(key, val)
        elif isinstance(msg, list):
            # Normal streaming messages
            # Typically msg is like ['TimingData', '{"Lines": ...}']
            if len(msg) >= 2:
                category = msg[0]
                try:
                    # signalrcore sometimes automatically parses the JSON into a dict, so we handle both cases
                    data = msg[1] if isinstance(msg[1], dict) else json.loads(msg[1])
                    self._update_state(category, data)
                except Exception as e:
                    # Log the exact error and a snippet of the payload to diagnose decompression or formatting issues
                    logger.error(f"Error parsing {category}: {e}. Raw data snippet: {str(msg[1])[:100]}")

    def _update_state(self, category, data):
        def deep_update(target, source):
            for k, v in source.items():
                if isinstance(v, dict) and k in target and isinstance(target[k], dict):
                    deep_update(target[k], v)
                else:
                    target[k] = v

        with state_lock:
            # For RaceControlMessages we might want to append, but for timing data we replace or deep update
            if category == "RaceControlMessages":
                if "Messages" in data:
                    msgs = data["Messages"]
                    if isinstance(msgs, dict):
                        live_timing_state["RaceControlMessages"].extend(msgs.values())
                    else:
                        live_timing_state["RaceControlMessages"].extend(msgs)
            else:
                # For dictionaries like TimingData, we can do a simple replace or dict update
                # Since we are returning raw data right now, a simple overwrite or update is okay.
                if isinstance(data, dict):
                    if category not in live_timing_state:
                        live_timing_state[category] = {}
                    
                    # Some categories like TimingData have "Lines" which contain per-driver updates
                    # We should deep update lines to not lose other drivers when only one updates
                    if "Lines" in data and category in ["TimingData", "TimingStats", "TimingAppData"]:
                        if "Lines" not in live_timing_state[category]:
                            live_timing_state[category]["Lines"] = {}
                        for driver_num, driver_data in data["Lines"].items():
                            if driver_num not in live_timing_state[category]["Lines"]:
                                live_timing_state[category]["Lines"][driver_num] = {}
                            deep_update(live_timing_state[category]["Lines"][driver_num], driver_data)
                        
                        # Process any other top-level keys (like SessionPart)
                        for k, v in data.items():
                            if k != "Lines":
                                if isinstance(v, dict) and k in live_timing_state[category] and isinstance(live_timing_state[category][k], dict):
                                    deep_update(live_timing_state[category][k], v)
                                else:
                                    live_timing_state[category][k] = v
                    else:
                        deep_update(live_timing_state[category], data)


def clear_live_timing_state():
    with state_lock:
        live_timing_state.clear()
        live_timing_state.update({
            "TimingData": {},
            "TimingStats": {},
            "TimingAppData": {},
            "DriverList": {},
            "TrackStatus": {},
            "WeatherData": {},
            "SessionInfo": {},
            "RaceControlMessages": []
        })

# Global instance
_client = None

def start_live_timing_client():
    def supervisor():
        global _client
        
        # We track the last time we successfully received a message across reconnects
        global_last_msg_time = time.time()
        
        while True:
            try:
                # Update our global message time if the client is active
                if _client is not None:
                    client_last_msg = getattr(_client, '_t_last_message', None)
                    if client_last_msg:
                        global_last_msg_time = client_last_msg

                current_time = time.time()

                # Clear data if it has been more than 1 hour (3600 seconds) since the last message
                if current_time - global_last_msg_time > 3600:
                    logger.warning("No messages for over 1 hour. Session assumed over, clearing old data...")
                    clear_live_timing_state()
                    # Reset the global timer so we don't spam clear
                    global_last_msg_time = current_time

                # Handle connection health
                if _client is None:
                    logger.info("Starting in-memory FastF1 Live Timing Client...")
                    # We NO LONGER clear state here. State is only cleared by the 1-hour timeout above.
                    _client = InMemorySignalRClient(timeout=0)
                    _client._run()
                else:
                    # Restart connection if explicitly disconnected
                    if not getattr(_client, '_is_connected', False):
                        logger.warning("Live timing connection closed. Restarting...")
                        try:
                            _client._exit()
                        except Exception:
                            pass
                        _client = None
                        
            except Exception as e:
                logger.error(f"Error in live timing supervisor: {e}")
                
            time.sleep(10)
            
    import threading
    supervisor_thread = threading.Thread(target=supervisor, daemon=True)
    supervisor_thread.start()
