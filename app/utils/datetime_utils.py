"""
Date and time parsing utilities.

Provides helper functions for parsing F1 schedule date/time strings
into timezone-aware datetime objects.
"""

from datetime import datetime, timezone


def parse_race_datetime(date_str, time_str="00:00:00Z"):
    """
    Parse a race date and time string into a timezone-aware datetime.

    Args:
        date_str: Date string in 'YYYY-MM-DD' format.
        time_str: Time string in 'HH:MM:SSZ' format. Defaults to midnight UTC.

    Returns:
        A timezone-aware datetime object in UTC.
    """
    combined = f"{date_str}T{time_str}"
    return datetime.fromisoformat(combined.replace('Z', '+00:00'))


def is_session_completed(date_str, time_str="00:00:00Z"):
    """
    Check if a session has already occurred.

    Args:
        date_str: Date string in 'YYYY-MM-DD' format.
        time_str: Time string in 'HH:MM:SSZ' format.

    Returns:
        True if the session datetime is in the past.
    """
    session_dt = parse_race_datetime(date_str, time_str)
    return session_dt < datetime.now(timezone.utc)
