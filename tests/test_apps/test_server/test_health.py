"""Tests for the health and status endpoints."""
import sys

sys.path.append(".")

import pytest
from fastapi.testclient import TestClient

from src.apps.server.app.testio_server import app
from src.apps.server.database.configuration_data import update_execution_manager_data
from src.core.execution.data import ExecutionManagerInputData


@pytest.fixture
def client():
    """Create a test client with basic test data."""
    update_execution_manager_data(
        {
            "program.py": [
                ExecutionManagerInputData(
                    command='python3 "program.py"',
                    input=[],
                    output=["Hello World"],
                    timeout=1,
                )
            ]
        }
    )
    with TestClient(app) as client:
        yield client


def test_health_endpoint(client):
    """Test the health check endpoint returns proper status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["version"] == "1.0.0"


def test_status_endpoint(client):
    """Test the API status endpoint returns proper information."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "timestamp" in data
    assert data["version"] == "1.0.0"
    assert "uptime_seconds" in data
    assert isinstance(data["uptime_seconds"], float)
    assert "database_connected" in data
