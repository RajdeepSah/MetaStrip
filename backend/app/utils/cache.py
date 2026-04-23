"""In-memory TTL cache for cleaned files.

Each entry is a dict:
    {"bytes": bytes, "mime_type": str, "filename": str}

Entries expire automatically after CACHE_TTL_SECONDS (default 15 min).
Keyed by UUID string assigned at strip time.

Note: single-process cache — run gunicorn with --workers 1 (the default
in docker-compose) so all requests share the same store.
"""
from __future__ import annotations

from typing import Any

from cachetools import TTLCache

_store: TTLCache | None = None


def init_cache(maxsize: int = 100, ttl: int = 900) -> None:
    global _store
    _store = TTLCache(maxsize=maxsize, ttl=ttl)


def put(key: str, value: Any) -> None:
    if _store is None:
        init_cache()
    assert _store is not None
    _store[key] = value


def get(key: str) -> Any | None:
    if _store is None:
        return None
    return _store.get(key)


def remove(key: str) -> None:
    if _store is not None:
        _store.pop(key, None)
