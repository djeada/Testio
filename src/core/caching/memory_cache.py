"""
In-memory cache implementation with TTL support.
Thread-safe and optimized for high-concurrency scenarios.
"""

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, TypeVar
from functools import wraps
import hashlib
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CacheEntry:
    """Represents a cached value with metadata."""
    value: Any
    created_at: float
    ttl: float
    hits: int = 0

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return time.time() - self.created_at > self.ttl


class MemoryCache:
    """
    Thread-safe in-memory cache with TTL support.
    Uses a dictionary with per-key locking for high concurrency.
    """

    def __init__(self, default_ttl: float = 300.0, max_size: int = 1000):
        """
        Initialize the memory cache.

        :param default_ttl: Default time-to-live in seconds (default: 5 minutes)
        :param max_size: Maximum number of entries in the cache
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._default_ttl = default_ttl
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.

        :param key: The cache key
        :return: The cached value or None if not found/expired
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._misses += 1
                return None

            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                return None

            entry.hits += 1
            self._hits += 1
            return entry.value

    def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[float] = None
    ) -> None:
        """
        Store a value in the cache.

        :param key: The cache key
        :param value: The value to cache
        :param ttl: Optional TTL override
        """
        with self._lock:
            # Evict expired entries if cache is full
            if len(self._cache) >= self._max_size:
                self._evict_expired()

            # If still full, evict least recently used
            if len(self._cache) >= self._max_size:
                self._evict_lru()

            self._cache[key] = CacheEntry(
                value=value,
                created_at=time.time(),
                ttl=ttl if ttl is not None else self._default_ttl
            )

    def delete(self, key: str) -> bool:
        """
        Remove a value from the cache.

        :param key: The cache key
        :return: True if the key was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all entries from the cache."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        :return: Dictionary with cache statistics
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 2),
                "default_ttl": self._default_ttl
            }

    def _evict_expired(self) -> int:
        """
        Remove all expired entries.

        :return: Number of entries evicted
        """
        expired_keys = [
            key for key, entry in self._cache.items() 
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)

    def _evict_lru(self) -> None:
        """Evict the least recently used entry based on hit count."""
        if not self._cache:
            return

        # Find the entry with fewest hits
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].hits
        )
        del self._cache[lru_key]


# Global cache instance
_global_cache: Optional[MemoryCache] = None
_global_cache_lock = threading.Lock()


def get_global_cache() -> MemoryCache:
    """
    Get or create the global cache instance.

    :return: The global MemoryCache instance
    """
    global _global_cache
    if _global_cache is None:
        with _global_cache_lock:
            if _global_cache is None:
                _global_cache = MemoryCache()
    return _global_cache


def cache_result(
    ttl: Optional[float] = None,
    key_prefix: str = "",
    cache: Optional[MemoryCache] = None
) -> Callable:
    """
    Decorator to cache function results.

    :param ttl: Time-to-live for cached results
    :param key_prefix: Prefix for cache keys
    :param cache: Optional cache instance (uses global cache if not provided)
    :return: Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Build cache key from function name and arguments
            key_parts = [key_prefix or func.__module__, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            raw_key = ":".join(key_parts)
            cache_key = hashlib.md5(raw_key.encode()).hexdigest()

            cache_instance = cache or get_global_cache()

            # Try to get from cache
            cached_value = cache_instance.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_instance.set(cache_key, result, ttl)
            logger.debug(f"Cached result for {func.__name__}")
            return result

        return wrapper
    return decorator
