"""Tests for the metrics collector module."""
import sys
import time
import threading

sys.path.append(".")

import pytest

from src.core.metrics.collector import MetricsCollector, get_metrics_collector


class TestMetricsCollector:
    """Test suite for MetricsCollector class."""

    def test_increment_counter(self):
        """Test incrementing a counter."""
        collector = MetricsCollector()
        collector.increment("requests")
        collector.increment("requests")
        collector.increment("requests", 5)
        assert collector.get_counter("requests") == 7

    def test_decrement_counter(self):
        """Test decrementing a counter."""
        collector = MetricsCollector()
        collector.increment("connections", 10)
        collector.decrement("connections", 3)
        assert collector.get_counter("connections") == 7

    def test_get_nonexistent_counter(self):
        """Test getting a counter that doesn't exist returns 0."""
        collector = MetricsCollector()
        assert collector.get_counter("nonexistent") == 0

    def test_set_gauge(self):
        """Test setting a gauge value."""
        collector = MetricsCollector()
        collector.set_gauge("cpu_usage", 45.5)
        assert collector.get_gauge("cpu_usage") == 45.5
        collector.set_gauge("cpu_usage", 50.0)
        assert collector.get_gauge("cpu_usage") == 50.0

    def test_get_nonexistent_gauge(self):
        """Test getting a gauge that doesn't exist returns None."""
        collector = MetricsCollector()
        assert collector.get_gauge("nonexistent") is None

    def test_record_timing(self):
        """Test recording timing measurements."""
        collector = MetricsCollector()
        collector.record_timing("db_query", 0.05)
        collector.record_timing("db_query", 0.10)
        collector.record_timing("db_query", 0.15)
        
        timing = collector.get_timing("db_query")
        assert timing["count"] == 3
        assert timing["min_ms"] == 50.0  # 0.05s = 50ms
        assert timing["max_ms"] == 150.0  # 0.15s = 150ms
        assert timing["avg_ms"] == 100.0  # (50+100+150)/3 = 100ms

    def test_timer_context_manager(self):
        """Test the timer context manager."""
        collector = MetricsCollector()
        
        with collector.timer("operation"):
            time.sleep(0.05)  # Sleep for 50ms
        
        timing = collector.get_timing("operation")
        assert timing["count"] == 1
        assert timing["min_ms"] >= 50.0  # At least 50ms

    def test_timed_decorator(self):
        """Test the timed decorator."""
        collector = MetricsCollector()

        @collector.timed("my_function")
        def slow_function():
            time.sleep(0.05)
            return "done"

        result = slow_function()
        assert result == "done"
        
        timing = collector.get_timing("my_function")
        assert timing["count"] == 1
        assert timing["min_ms"] >= 50.0

    def test_get_all_metrics(self):
        """Test getting all collected metrics."""
        collector = MetricsCollector()
        collector.increment("requests", 10)
        collector.set_gauge("memory", 512.0)
        collector.record_timing("latency", 0.1)
        
        all_metrics = collector.get_all_metrics()
        
        assert "uptime_seconds" in all_metrics
        assert "counters" in all_metrics
        assert "gauges" in all_metrics
        assert "timings" in all_metrics
        assert all_metrics["counters"]["requests"] == 10
        assert all_metrics["gauges"]["memory"] == 512.0

    def test_reset(self):
        """Test resetting all metrics."""
        collector = MetricsCollector()
        collector.increment("requests", 100)
        collector.set_gauge("memory", 512.0)
        collector.record_timing("latency", 0.1)
        
        collector.reset()
        
        assert collector.get_counter("requests") == 0
        assert collector.get_gauge("memory") is None
        assert collector.get_timing("latency") is None

    def test_thread_safety(self):
        """Test that metrics operations are thread-safe."""
        collector = MetricsCollector()
        errors = []

        def increment_worker():
            try:
                for _ in range(1000):
                    collector.increment("concurrent")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=increment_worker) for _ in range(10)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert collector.get_counter("concurrent") == 10000


class TestTimingStats:
    """Test suite for timing statistics calculations."""

    def test_percentile_calculation(self):
        """Test percentile calculation."""
        collector = MetricsCollector()
        
        # Add 100 samples from 1 to 100
        for i in range(1, 101):
            collector.record_timing("test", i / 1000)  # Convert to seconds
        
        timing = collector.get_timing("test")
        
        # P50 should be around 50ms
        assert 40 <= timing["p50_ms"] <= 60
        # P95 should be around 95ms
        assert 90 <= timing["p95_ms"] <= 100
        # P99 should be around 99ms
        assert 95 <= timing["p99_ms"] <= 100


class TestGlobalMetrics:
    """Test the global metrics collector singleton."""

    def test_global_singleton(self):
        """Test that get_metrics_collector returns the same instance."""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()
        assert collector1 is collector2
