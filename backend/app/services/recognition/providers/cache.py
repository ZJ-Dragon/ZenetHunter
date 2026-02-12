"""LRU cache with TTL for external recognition results."""

import hashlib
import json
import logging
from collections import OrderedDict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RecognitionCache:
    """LRU cache with TTL for recognition results."""

    def __init__(
        self,
        max_size: int = 1000,
        ttl_hours: int = 24 * 7,  # 7 days default
        cache_dir: Path | None = None,
    ):
        """
        Initialize recognition cache.

        Args:
            max_size: Maximum number of cached entries (LRU eviction)
            ttl_hours: Time-to-live in hours
            cache_dir: Optional directory for persistent cache (disabled by default)
        """
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)
        self._cache: OrderedDict[str, tuple[datetime, Any]] = OrderedDict()
        self.cache_dir = cache_dir
        self._load_persistent_cache()

    def _get_cache_key(self, provider: str, query: str) -> str:
        """
        Generate cache key from provider and query.

        Args:
            provider: Provider name
            query: Query string (OUI or fingerprint hash)

        Returns:
            Cache key string
        """
        # Hash the query to avoid storing sensitive data in key
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        return f"{provider}:{query_hash}"

    def _load_persistent_cache(self):
        """Load cache from disk if cache_dir is set."""
        if not self.cache_dir:
            return

        try:
            cache_file = self.cache_dir / "recognition_cache.json"
            if not cache_file.exists():
                return

            with open(cache_file, encoding="utf-8") as f:
                data = json.load(f)

            now = datetime.now(UTC)
            for key, (expiry_str, value) in data.items():
                expiry = datetime.fromisoformat(expiry_str)
                if expiry > now:
                    self._cache[key] = (expiry, value)
                # Expired entries are not loaded

            logger.info(f"Loaded {len(self._cache)} entries from persistent cache")
        except Exception as e:
            logger.warning(f"Failed to load persistent cache: {e}")

    def _save_persistent_cache(self):
        """Save cache to disk if cache_dir is set."""
        if not self.cache_dir:
            return

        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = self.cache_dir / "recognition_cache.json"

            data = {
                key: (expiry.isoformat(), value)
                for key, (expiry, value) in self._cache.items()
            }

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(data)} entries to persistent cache")
        except Exception as e:
            logger.warning(f"Failed to save persistent cache: {e}")

    def get(self, provider: str, query: str) -> Any | None:
        """
        Get cached result.

        Args:
            provider: Provider name
            query: Query string

        Returns:
            Cached value or None if not found/expired
        """
        key = self._get_cache_key(provider, query)

        if key not in self._cache:
            return None

        expiry, value = self._cache[key]
        now = datetime.now(UTC)

        if expiry < now:
            # Expired - remove from cache
            del self._cache[key]
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        return value

    def set(self, provider: str, query: str, value: Any):
        """
        Cache a result.

        Args:
            provider: Provider name
            query: Query string
            value: Value to cache
        """
        key = self._get_cache_key(provider, query)
        expiry = datetime.now(UTC) + self.ttl

        # Remove if exists (will be re-added at end)
        if key in self._cache:
            del self._cache[key]

        # Add new entry
        self._cache[key] = (expiry, value)

        # Evict oldest if over limit
        while len(self._cache) > self.max_size:
            self._cache.popitem(last=False)

        # Save to disk periodically (every 10 writes)
        if len(self._cache) % 10 == 0:
            self._save_persistent_cache()

    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()
        if self.cache_dir:
            cache_file = self.cache_dir / "recognition_cache.json"
            if cache_file.exists():
                cache_file.unlink()

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        now = datetime.now(UTC)
        expired_count = sum(1 for expiry, _ in self._cache.values() if expiry < now)
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "expired_entries": expired_count,
            "ttl_hours": self.ttl.total_seconds() / 3600,
        }


# Global cache instance
_cache_instance: RecognitionCache | None = None


def get_recognition_cache() -> RecognitionCache:
    """Get global recognition cache instance."""
    global _cache_instance
    if _cache_instance is None:
        # Cache directory: backend/data/cache (gitignored)
        cache_dir = Path(__file__).parent.parent.parent.parent / "data" / "cache"
        _cache_instance = RecognitionCache(
            max_size=1000,
            ttl_hours=24 * 7,  # 7 days
            cache_dir=cache_dir,
        )
    return _cache_instance
