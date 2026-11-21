import json
import logging
import threading
import time
from datetime import datetime, timezone
from fastf1.livetiming.client import SignalRClient
from signalrcore.messages.completion_message import CompletionMessage

logger = logging.getLogger("InMemoryLiveTiming")
logger.setLevel(logging.INFO)
logger.propagate = False
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

feed_diagnostics = {
    "connection_state": "starting",
    "connected_since": None,
    "last_message_at": None,
    "message_count": 0,
    "last_topic": None,
    "topic_counts": {},
    "last_error": None,
}


def _set_connection_state(state, error=None):
    with state_lock:
        feed_diagnostics["connection_state"] = state
        feed_diagnostics["last_error"] = error
        if state == "connected":
            feed_diagnostics["connected_since"] = time.time()
        elif state != "connected":
            feed_diagnostics["connected_since"] = None


def get_live_feed_status():
    """Return safe, lightweight diagnostics for the live timing test page."""
    now = time.time()
    with state_lock:
        last_message_at = feed_diagnostics["last_message_at"]
        timing_lines = live_timing_state.get("TimingData", {}).get("Lines", {})
        status = dict(feed_diagnostics)
        status["topic_counts"] = dict(feed_diagnostics["topic_counts"])
        status["connected"] = status["connection_state"] == "connected"
        status["last_message_age_seconds"] = (
            round(max(0, now - last_message_at), 1) if last_message_at else None
        )
        status["last_message_at"] = (
            datetime.fromtimestamp(last_message_at, timezone.utc).isoformat()
            if last_message_at else None
        )
        status["connected_since"] = (
            datetime.fromtimestamp(status["connected_since"], timezone.utc).isoformat()
            if status["connected_since"] else None
        )
        status["driver_count"] = len(timing_lines)
        return status

class InMemorySignalRClient(SignalRClient):
    def __init__(self, timeout=60, logger=None):
        # We pass a dummy filename since we'll override file writing
        super().__init__("dummy.txt", filemode='w', timeout=timeout, logger=logger)
        
    def _run(self):
        # Override _run to not open a file
        import os
        import requests
        from signalrcore.hub_connection_builder import HubConnectionBuilder
        
        # Pre-negotiate to the get a valid AWSALBCORS header token
        r = requests.options(self._negotiate_url, headers=self.headers, timeout=15)
        # FastF1's SignalR setup intentionally uses this OPTIONS request only to
        # obtain the load-balancer cookie. F1 may answer 405 while still setting it.
        cookie = r.cookies.get("AWSALBCORS")
        if not cookie:
            raise RuntimeError("F1 live timing negotiate response did not include AWSALBCORS")
        self.headers.update(
            {"Cookie": f"AWSALBCORS={cookie}"}
        )

        configured_token = os.getenv("F1_AUTH_TOKEN")
        if configured_token:
            access_token_factory = lambda: configured_token.strip()
        elif hasattr(self, "_access_token_factory"):
            # FastF1 3.9+ moved account auth into SignalRClient's helper.
            access_token_factory = self._access_token_factory()
        else:
            # Compatibility with older FastF1 releases still used locally.
            from fastf1.internals.f1auth import get_auth_token
            access_token_factory = get_auth_token

        # Configure and create connection
        options = {
            "verify_ssl": True,
            "headers": self.headers
        }
        if not self._no_auth and access_token_factory is not None:
            options["access_token_factory"] = access_token_factory

        self._connection = HubConnectionBuilder() \
            .with_url(self._connection_url, options=options) \
            .configure_logging(logging.INFO) \
            .build()

        self._connection.on_open(self._on_connect)
        self._connection.on_close(self._on_close)
        self._connection.on('feed', self._on_message)

        self._connection.start()

        # wait for connection to be established
        connect_deadline = time.monotonic() + 30
        while not self._is_connected:
            if time.monotonic() >= connect_deadline:
                try:
                    self._connection.stop()
                except Exception:
                    pass
                raise TimeoutError("Timed out waiting for the F1 live timing SignalR connection")
            time.sleep(0.1)

        self._connection.send(
            "Subscribe", [self.topics], on_invocation=self._on_message
        )

    def _exit(self):
        self._connection.stop()
        # No file to close

    def _on_connect(self):
        super()._on_connect()
        _set_connection_state("connected")

    def _on_close(self):
        super()._on_close()
        _set_connection_state("disconnected")

    def _on_message(self, msg):
        received_at = time.time()
        self._t_last_message = received_at

        topics = []
        if isinstance(msg, CompletionMessage) and isinstance(msg.result, dict):
            topics = list(msg.result.keys())
        elif isinstance(msg, list) and msg:
            topics = [str(msg[0])]
        with state_lock:
            feed_diagnostics["last_message_at"] = received_at
            feed_diagnostics["message_count"] += 1
            feed_diagnostics["last_topic"] = topics[-1] if topics else "initial sync"
            for topic in topics:
                counts = feed_diagnostics["topic_counts"]
                counts[topic] = counts.get(topic, 0) + 1
            feed_diagnostics["last_error"] = None
        
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
                    with state_lock:
                        feed_diagnostics["last_error"] = f"Could not parse {category} message ({type(e).__name__})"

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
        
        # Keep the last received-message timestamp across reconnect attempts. A stale
        # client must not reset this clock, otherwise stale-state cleanup repeats forever.
        global_last_msg_time = time.time()
        state_cleared_for_stale_feed = False
        reconnect_after_seconds = 60
        
        while True:
            try:
                # Update our global message time if the client is active
                if _client is not None:
                    client_last_msg = getattr(_client, '_t_last_message', None)
                    if client_last_msg and client_last_msg > global_last_msg_time:
                        global_last_msg_time = client_last_msg
                        state_cleared_for_stale_feed = False

                current_time = time.time()

                # Clear stale data once per no-message period, not on every loop.
                if (current_time - global_last_msg_time > 3600
                        and not state_cleared_for_stale_feed):
                    logger.warning("No messages for over 1 hour. Session assumed over, clearing old data...")
                    clear_live_timing_state()
                    state_cleared_for_stale_feed = True

                # Handle connection health
                if _client is None:
                    logger.info("Starting in-memory FastF1 Live Timing Client...")
                    _set_connection_state("connecting")
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
                    elif current_time - global_last_msg_time > reconnect_after_seconds:
                        logger.warning(
                            "No live timing messages for %s seconds. Reconnecting...",
                            reconnect_after_seconds,
                        )
                        try:
                            _client._exit()
                        except Exception:
                            pass
                        _client = None
                        
            except Exception as e:
                logger.exception("Error in live timing supervisor: %s", e)
                _set_connection_state("error", type(e).__name__)
                if _client is not None:
                    try:
                        _client._exit()
                    except Exception:
                        pass
                    _client = None
                
            time.sleep(10)
            
    import threading
    supervisor_thread = threading.Thread(target=supervisor, daemon=True)
    supervisor_thread.start()
