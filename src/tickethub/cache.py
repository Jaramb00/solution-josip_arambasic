"""Jednostavan in-memory TTL cache (bez vanjskih ovisnosti)
"""

import time
from typing import Any

from tickethub.config import settings


class TTLCache:
    def __init__(self, ttl_seconds: float) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if item is None:
            return None
        expires_at, value = item
        if time.monotonic() >= expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.monotonic() + self._ttl, value)

    def clear(self) -> None:
        self._store.clear()


# Zajednička instanca za agregirane odgovore (npr. /stats).
stats_cache = TTLCache(settings.cache_ttl_seconds)
