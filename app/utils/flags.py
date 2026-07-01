"""
Country flag utility.

Converts F1 country names to flag emoji using the `flag` library.
"""

import flag
from app.core.constants import COUNTRY_ISO_MAPPING
from app.core.logging import logger


def get_clean_flag(country_name):
    """
    Convert a country name to its flag emoji.

    Uses the COUNTRY_ISO_MAPPING for F1-specific country names,
    falling back to the first two characters uppercased as an ISO code guess.

    Args:
        country_name: The country name from the Jolpica API.

    Returns:
        Flag emoji string, or 🏁 if conversion fails.
    """
    iso_code = COUNTRY_ISO_MAPPING.get(country_name, country_name[:2].upper())

    try:
        return flag.flag(iso_code)
    except Exception as e:
        logger.warning(
            f"Flag lookup failed for {repr(country_name)} "
            f"with iso_code {repr(iso_code)}: {type(e).__name__} - {e}"
        )
        return "🏁"
