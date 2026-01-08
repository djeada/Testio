"""
Metrics collector for performance monitoring.
Provides counters, histograms, and timing measurements.
"""

import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generator, List, Optional
from functools import wraps
import logging
import statistics

logger = logging.getLogger(__name__)


@dataclass
class TimingStats:
    """Statistics for timing measurements."""
    count: int = 0
    total_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    samples: List[float] = field(default_factory=list)
    max_samples: int = 1000

    def record(self, duration: float) -> None:
        """Record a new timing measurement."""
        self.count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        
        # Keep only recent samples for percentile calculation
        if len(self.samples) >= self.max_samples:
            self.samples.pop(0)
        self.samples.append(duration)

    @property
    def avg_time(self) -> float:
        """Calculate average time."""
        return self.total_time / self.count if self.count > 0 else 0.0

    def percentile(self, p: float) -> float:
        """Calculate percentile value."""
        if not self.samples:
            return 0.0
        sorted_samples = sorted(self.samples)
        index = int(len(sorted_samples) * p / 100)
        return sorted_samples[min(index, len(sorted_samples) - 1)]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            "count": self.count,
            "total_ms": round(self.total_time * 1000, 2),
            "avg_ms": round(self.avg_time * 1000, 2),
            "min_ms": round(self.min_time * 1000, 2) if self.min_time != float("inf") else 0,
            "max_ms": round(self.max_time * 1000, 2),
            "p50_ms": round(self.percentile(50) * 1000, 2),
            "p95_ms": round(self.percentile(95) * 1000, 2),
            "p99_ms": round(self.percentile(99) * 1000, 2),
        }


class MetricsCollector:
    """
    Collects and aggregates performance metrics.
    Thread-safe implementation for concurrent access.
    """

    def __init__(self):
        """Initialize the metrics collector."""
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._timings: Dict[str, TimingStats] = defaultdict(TimingStats)
        self._lock = threading.RLock()
        self._start_time = time.time()

    def increment(self, name: str, value: int = 1) -> None:
        """
        Increment a counter.

        :param name: Counter name
        :param value: Amount to increment (default: 1)
        """
        with self._lock:
            self._counters[name] += value

    def decrement(self, name: str, value: int = 1) -> None:
        """
        Decrement a counter.

        :param name: Counter name
        :param value: Amount to decrement (default: 1)
        """
        with self._lock:
            self._counters[name] -= value

    def set_gauge(self, name: str, value: float) -> None:
        """
        Set a gauge value.

        :param name: Gauge name
        :param value: Value to set
        """
        with self._lock:
            self._gauges[name] = value

    def record_timing(self, name: str, duration: float) -> None:
        """
        Record a timing measurement.

        :param name: Timing name
        :param duration: Duration in seconds
        """
        with self._lock:
            self._timings[name].record(duration)

    @contextmanager
    def timer(self, name: str) -> Generator[None, None, None]:
        """
        Context manager for timing code blocks.

        :param name: Timing name
        """
        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            self.record_timing(name, duration)

    def timed(self, name: Optional[str] = None) -> Callable:
        """
        Decorator for timing function execution.

        :param name: Optional timing name (defaults to function name)
        :return: Decorated function
        """
        def decorator(func: Callable) -> Callable:
            timing_name = name or f"{func.__module__}.{func.__name__}"

            @wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                try:
                    return func(*args, **kwargs)
                finally:
                    duration = time.time() - start
                    self.record_timing(timing_name, duration)

            return wrapper
        return decorator

    def get_counter(self, name: str) -> int:
        """
        Get a counter value.

        :param name: Counter name
        :return: Counter value
        """
        with self._lock:
            return self._counters.get(name, 0)

    def get_gauge(self, name: str) -> Optional[float]:
        """
        Get a gauge value.

        :param name: Gauge name
        :return: Gauge value or None
        """
        with self._lock:
            return self._gauges.get(name)

    def get_timing(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get timing statistics.

        :param name: Timing name
        :return: Timing stats dictionary or None
        """
        with self._lock:
            if name in self._timings:
                return self._timings[name].to_dict()
            return None

    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all collected metrics.

        :return: Dictionary with all metrics
        """
        with self._lock:
            uptime = time.time() - self._start_time
            return {
                "uptime_seconds": round(uptime, 2),
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "timings": {
                    name: stats.to_dict() 
                    for name, stats in self._timings.items()
                }
            }

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._timings.clear()
            self._start_time = time.time()


# Global metrics instance
_global_metrics: Optional[MetricsCollector] = None
_metrics_lock = threading.Lock()


def get_metrics_collector() -> MetricsCollector:
    """
    Get or create the global metrics collector.

    :return: The global MetricsCollector instance
    """
    global _global_metrics
    if _global_metrics is None:
        with _metrics_lock:
            if _global_metrics is None:
                _global_metrics = MetricsCollector()
    return _global_metrics
