"""Tests for the metrics routes."""
import sys

sys.path.append(".")

import pytest
from fastapi.testclient import TestClient

from src.apps.server.app.testio_server import create_app


@pytest.fixture
def client():
    """Create a test client with the teacher mode app."""
    app = create_app(mode="teacher")
    with TestClient(app) as client:
        yield client


class TestMetricsEndpoints:
    """Test suite for metrics API endpoints."""

    def test_get_metrics(self, client):
        """Test the metrics endpoint returns proper data."""
        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()
        
        assert data["application"] == "Testio"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data
        assert "metrics" in data
        assert "counters" in data["metrics"]
        assert "gauges" in data["metrics"]
        assert "timings" in data["metrics"]

    def test_get_cache_stats(self, client):
        """Test the cache stats endpoint."""
        response = client.get("/api/metrics/cache")
        assert response.status_code == 200
        data = response.json()
        
        assert "timestamp" in data
        assert "cache_stats" in data
        assert "size" in data["cache_stats"]
        assert "max_size" in data["cache_stats"]
        assert "hits" in data["cache_stats"]
        assert "misses" in data["cache_stats"]

    def test_get_system_stats(self, client):
        """Test the system stats endpoint."""
        response = client.get("/api/metrics/system")
        assert response.status_code == 200
        data = response.json()
        
        assert "timestamp" in data
        assert "database" in data
        assert "execution_queue" in data
        assert "rate_limiter" in data

    def test_reset_metrics(self, client):
        """Test resetting metrics."""
        # First, make some requests to generate metrics
        client.get("/health")
        client.get("/api/metrics")
        
        # Reset metrics
        response = client.post("/api/metrics/reset")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        # Verify metrics are reset
        response = client.get("/api/metrics")
        data = response.json()
        # After reset, counters should be empty or reset
        assert "metrics" in data
