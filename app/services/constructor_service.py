"""
Constructor service.

Responsible for fetching and processing constructor (team) information.
"""

from app.core.config import CONSTRUCTORS_URL
from app.core.http_client import http_client


def get_constructors():
    """
    Fetch and clean the current season's constructor lineup.

    Returns:
        Dict with season, total constructor count, and cleaned constructors list.

    Raises:
        requests.exceptions.RequestException: On API fetch failure.
    """
    data = http_client.fetch_json(CONSTRUCTORS_URL)
    constructors_raw = data["MRData"]["ConstructorTable"]["Constructors"]

    clean_constructors = []
    for constructor in constructors_raw:
        constructor_entry = {
            "constructorid": constructor["constructorId"],
            "name": constructor["name"],
            "nationality": constructor["nationality"],
            "url": constructor["url"]
        }
        clean_constructors.append(constructor_entry)

    return {
        "season": data["MRData"]["ConstructorTable"]["season"],
        "total_constructors": len(clean_constructors),
        "constructors": clean_constructors
    }
