"""In-memory TTL cache for cleaned files.

Keyed by UUID string. Each entry holds the raw bytes of a stripped file.
Entries expire automatically after CACHE_TTL_SECONDS (default 15 min).

Note: this is a single-process cache. Run gunicorn with --workers 1
(the default in docker-compose) so all requests share the same store.
"""
from __future__ import annotations

from cachetools import TTLCache

# Populated lazily via init_cache() so the app config drives the settings.
_store: TTLCache | None = None


def init_cache(maxsize: int = 100, ttl: int = 900) -> None:
    global _store
    _store = TTLCache(maxsize=maxsize, ttl=ttl)


def put(key: str, value: bytes) -> None:
    if _store is None:
        init_cache()
    assert _store is not None
    _store[key] = value


def get(key: str) -> bytes | None:
    if _store is None:
        return None
    return _store.get(key)


def remove(key: str) -> None:
    if _store is not None:
        _store.pop(key, None)
