"""Tests for the batch execution endpoint."""
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


def test_batch_execute_single_config(client):
    """Test batch execution with a single configuration."""
    request_data = {
        "configurations": [
            {
                "name": "test_hello",
                "command": "python3",
                "code": "print('Hello World')",
                "tests": [
                    {
                        "input": [],
                        "output": ["Hello World"],
                        "timeout": 5
                    }
                ]
            }
        ]
    }
    
    response = client.post("/api/batch/execute", json=request_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_configurations"] == 1
    assert data["total_tests"] == 1
    assert data["total_passed"] == 1
    assert data["overall_score"] == 100.0
    
    results = data["results"]
    assert len(results) == 1
    assert results[0]["name"] == "test_hello"
    assert results[0]["passed_tests"] == 1


def test_batch_execute_multiple_configs(client):
    """Test batch execution with multiple configurations."""
    request_data = {
        "configurations": [
            {
                "name": "test_hello",
                "command": "python3",
                "code": "print('Hello World')",
                "tests": [
                    {
                        "input": [],
                        "output": ["Hello World"],
                        "timeout": 5
                    }
                ]
            },
            {
                "name": "test_add",
                "command": "python3",
                "code": "a = int(input())\nb = int(input())\nprint(a + b)",
                "tests": [
                    {
                        "input": ["5", "3"],
                        "output": ["8"],
                        "timeout": 5
                    }
                ]
            }
        ]
    }
    
    response = client.post("/api/batch/execute", json=request_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_configurations"] == 2
    assert data["total_tests"] == 2


def test_batch_execute_with_failure(client):
    """Test batch execution with a failing test."""
    request_data = {
        "configurations": [
            {
                "name": "test_wrong_output",
                "command": "python3",
                "code": "print('Wrong Output')",
                "tests": [
                    {
                        "input": [],
                        "output": ["Hello World"],
                        "timeout": 5
                    }
                ]
            }
        ]
    }
    
    response = client.post("/api/batch/execute", json=request_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_passed"] == 0
    assert data["overall_score"] == 0.0
    
    results = data["results"]
    assert results[0]["failed_tests"] == 1
    assert results[0]["test_results"][0]["passed"] == False


def test_batch_execute_empty_configurations(client):
    """Test batch execution with empty configurations list."""
    request_data = {"configurations": []}
    
    response = client.post("/api/batch/execute", json=request_data)
    assert response.status_code == 400
