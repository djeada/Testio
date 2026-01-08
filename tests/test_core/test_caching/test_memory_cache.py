"""Tests for the memory cache module."""
import sys
import time
import threading

sys.path.append(".")

import pytest

from src.core.caching.memory_cache import MemoryCache, cache_result


class TestMemoryCache:
    """Test suite for MemoryCache class."""

    def test_get_set_basic(self):
        """Test basic get and set operations."""
        cache = MemoryCache()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist returns None."""
        cache = MemoryCache()
        assert cache.get("nonexistent") is None

    def test_delete_key(self):
        """Test deleting a key from cache."""
        cache = MemoryCache()
        cache.set("key1", "value1")
        assert cache.delete("key1") is True
        assert cache.get("key1") is None
        assert cache.delete("key1") is False

    def test_clear_cache(self):
        """Test clearing all entries from cache."""
        cache = MemoryCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_ttl_expiration(self):
        """Test that entries expire after TTL."""
        cache = MemoryCache(default_ttl=0.1)  # 100ms TTL
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        time.sleep(0.15)  # Wait for expiration
        assert cache.get("key1") is None

    def test_custom_ttl_per_key(self):
        """Test setting custom TTL per key."""
        cache = MemoryCache(default_ttl=1.0)
        cache.set("short", "value", ttl=0.1)
        cache.set("long", "value", ttl=2.0)
        time.sleep(0.15)
        assert cache.get("short") is None
        assert cache.get("long") == "value"

    def test_max_size_eviction(self):
        """Test that entries are evicted when max size is reached."""
        cache = MemoryCache(max_size=3)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        # Access key1 and key2 to increase their hit count
        cache.get("key1")
        cache.get("key2")
        # Add a fourth entry
        cache.set("key4", "value4")
        stats = cache.get_stats()
        assert stats["size"] <= 3

    def test_stats_tracking(self):
        """Test that cache statistics are tracked correctly."""
        cache = MemoryCache()
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["size"] == 1

    def test_thread_safety(self):
        """Test that cache operations are thread-safe."""
        cache = MemoryCache()
        errors = []

        def writer(n):
            try:
                for i in range(100):
                    cache.set(f"key_{n}_{i}", f"value_{n}_{i}")
            except Exception as e:
                errors.append(e)

        def reader(n):
            try:
                for i in range(100):
                    cache.get(f"key_{n}_{i}")
            except Exception as e:
                errors.append(e)

        threads = []
        for n in range(5):
            threads.append(threading.Thread(target=writer, args=(n,)))
            threads.append(threading.Thread(target=reader, args=(n,)))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestCacheDecorator:
    """Test suite for cache_result decorator."""

    def test_function_result_cached(self):
        """Test that function results are cached."""
        call_count = 0

        @cache_result(ttl=60.0)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_function(5)
        result2 = expensive_function(5)
        
        assert result1 == 10
        assert result2 == 10
        assert call_count == 1  # Function called only once

    def test_different_args_different_cache(self):
        """Test that different arguments result in different cache entries."""
        call_count = 0

        @cache_result(ttl=60.0)
        def add(a, b):
            nonlocal call_count
            call_count += 1
            return a + b

        add(1, 2)
        add(1, 2)
        add(3, 4)
        
        assert call_count == 2  # Two unique calls

    def test_cache_with_kwargs(self):
        """Test that keyword arguments are included in cache key."""
        call_count = 0

        @cache_result(ttl=60.0)
        def greet(name, greeting="Hello"):
            nonlocal call_count
            call_count += 1
            return f"{greeting}, {name}!"

        greet("Alice")
        greet("Alice")
        greet("Alice", greeting="Hi")
        
        assert call_count == 2
