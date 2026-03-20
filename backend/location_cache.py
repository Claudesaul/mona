"""Cache for location and account names, used for suggestion questions and system prompt context."""

import logging
import time
from db.connections import execute_postgres_query, execute_salesforce_query

logger = logging.getLogger(__name__)

_cache = {
    "locations": [],
    "accounts": [],
    "loaded_at": 0,
    "rendered_context": "",
}

TTL = 3600  # Refresh every hour


def _ensure_loaded():
    """Load cache if stale or never loaded."""
    if time.time() - _cache["loaded_at"] > TTL:
        _load()


def get_names() -> dict:
    """Return cached location and account names, fetching if needed."""
    _ensure_loaded()
    return {"locations": _cache["locations"], "accounts": _cache["accounts"]}


def _load():
    """Fetch location names from OOS and account names from Salesforce."""
    # OOS locations (fastest — small view, ~523 rows)
    try:
        rows = execute_postgres_query(
            'SELECT DISTINCT "Location" FROM v_daily_oos ORDER BY "Location" LIMIT 500'
        )
        _cache["locations"] = [r["Location"] for r in rows if r.get("Location")]
        logger.info("Cached %d location names from OOS", len(_cache["locations"]))
    except Exception as e:
        logger.warning("Failed to load OOS locations: %s", e)

    # Salesforce accounts (customers + prospects)
    try:
        rows = execute_salesforce_query(
            "SELECT Name, Type FROM Account ORDER BY Name LIMIT 200"
        )
        _cache["accounts"] = [r["Name"] for r in rows if r.get("Name")]
        logger.info("Cached %d account names from Salesforce", len(_cache["accounts"]))
    except Exception as e:
        logger.warning("Failed to load Salesforce accounts: %s", e)

    # Pre-render the context string for the system prompt
    parts = []
    if _cache["locations"]:
        parts.append("Known locations: " + ", ".join(_cache["locations"]))
    if _cache["accounts"]:
        parts.append("Known Salesforce accounts: " + ", ".join(_cache["accounts"]))
    if parts:
        _cache["rendered_context"] = (
            "\n\n## Known names (for fuzzy matching and disambiguation)\n\n"
            "When users mention a location or account name with typos or partial matches, "
            "use this list to identify the correct one. If multiple matches exist (e.g. "
            "multiple 'House of Representatives' locations), ask the user which one they mean.\n\n"
            + "\n\n".join(parts)
        )
    else:
        _cache["rendered_context"] = ""

    _cache["loaded_at"] = time.time()


def get_location_context() -> str:
    """Return a compact string of location/account names for the system prompt."""
    _ensure_loaded()
    return _cache["rendered_context"]
