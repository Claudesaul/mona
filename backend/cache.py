"""Simple in-memory query result cache with TTL."""

import time
import hashlib
import json
import logging
from datetime import date

logger = logging.getLogger(__name__)

# Cache storage: {cache_key: {"result": str, "expires": float}}
_cache: dict[str, dict] = {}

# TTL in seconds
TTL_HISTORICAL = 3600  # 1 hour for queries about past dates
TTL_CURRENT = 300      # 5 minutes for queries about today/recent
TTL_STATIC = 1800      # 30 minutes for non-date queries (e.g., product_activity, warehouse inventory)

# Max cache entries to prevent memory bloat
MAX_ENTRIES = 200


def _make_key(tool_name: str, query: str) -> str:
    """Create a cache key from tool name and normalized query."""
    normalized = " ".join(query.strip().upper().split())
    raw = f"{tool_name}:{normalized}"
    return hashlib.md5(raw.encode()).hexdigest()


def _guess_ttl(query: str) -> int:
    """Guess appropriate TTL based on query content."""
    query_upper = query.upper()
    today_str = date.today().isoformat()

    # If query references today's date, use short TTL
    if today_str in query or "CURRENT_DATE" in query_upper or "GETDATE()" in query_upper or "NOW()" in query_upper:
        return TTL_CURRENT

    # If query has date filters with specific past dates, use long TTL
    if any(kw in query_upper for kw in ["WHERE", "FILTER"]) and any(
        kw in query_upper for kw in ["DATE", "TIME", "DATEKEY"]
    ):
        return TTL_HISTORICAL

    # Static/snapshot tables get medium TTL
    return TTL_STATIC


def get(tool_name: str, query: str) -> str | None:
    """Get cached result if available and not expired."""
    key = _make_key(tool_name, query)
    entry = _cache.get(key)

    if entry is None:
        return None

    if time.time() > entry["expires"]:
        del _cache[key]
        return None

    logger.info("Cache hit for %s query (key=%s)", tool_name, key[:8])
    return entry["result"]


def put(tool_name: str, query: str, result: str) -> None:
    """Cache a query result with auto-determined TTL."""
    # Don't cache errors
    try:
        parsed = json.loads(result)
        if "error" in parsed:
            return
    except (json.JSONDecodeError, TypeError):
        return

    # Evict oldest entries if at capacity
    if len(_cache) >= MAX_ENTRIES:
        oldest_key = min(_cache, key=lambda k: _cache[k]["expires"])
        del _cache[oldest_key]

    key = _make_key(tool_name, query)
    ttl = _guess_ttl(query)
    _cache[key] = {
        "result": result,
        "expires": time.time() + ttl,
    }
    logger.info("Cached %s query result (key=%s, ttl=%ds)", tool_name, key[:8], ttl)


def clear() -> None:
    """Clear entire cache."""
    _cache.clear()


def stats() -> dict:
    """Return cache stats."""
    now = time.time()
    active = sum(1 for e in _cache.values() if e["expires"] > now)
    return {"total_entries": len(_cache), "active_entries": active}
