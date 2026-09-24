"""
Metrics module for Testio.
Provides performance monitoring and metrics collection.
"""

from .collector import MetricsCollector, get_metrics_collector

__all__ = ["MetricsCollector", "get_metrics_collector"]
