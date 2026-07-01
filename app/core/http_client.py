"""
Shared HTTP client with connection pooling and error handling.

All HTTP requests throughout the project use this shared client instead
of calling requests.get() directly. Benefits include connection pooling,
persistent HTTP connections, centralized timeout configuration, and
reduced duplicate code.
"""

import requests
from app.core.logging import logger


class HttpClient:
    """Shared HTTP client backed by a requests.Session for connection pooling."""

    def __init__(self, timeout=30):
        self.session = requests.Session()
        self.timeout = timeout

    def fetch_json(self, url, timeout=None):
        """
        Fetch JSON data from a URL.

        Args:
            url: The URL to fetch from.
            timeout: Optional per-request timeout override.

        Returns:
            Parsed JSON response as a dict.

        Raises:
            requests.exceptions.RequestException: On network/HTTP errors.
        """
        response = self.session.get(url, timeout=timeout or self.timeout)
        response.raise_for_status()
        return response.json()

    def fetch_json_safe(self, url, default=None, timeout=None):
        """
        Fetch JSON data from a URL, returning a default value on failure.

        This is used for non-critical requests where a failure should not
        crash the parent operation (e.g., fetching weather data).

        Args:
            url: The URL to fetch from.
            default: Value to return on failure (defaults to None).
            timeout: Optional per-request timeout override.

        Returns:
            Parsed JSON response, or `default` on any error.
        """
        try:
            return self.fetch_json(url, timeout=timeout)
        except Exception as e:
            logger.warning(f"Non-critical request failed for {url}: {e}")
            return default


# Singleton instance — import this throughout the app
http_client = HttpClient()
