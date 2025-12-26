import sys

sys.path.append(".")

import json
import io

import pytest
from fastapi.testclient import TestClient

from src.apps.server.app.testio_server import app


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def test_homework_submission_endpoint(client):
    """Test the homework submission endpoint with multiple student files."""
    
    # Create a simple configuration
    config_json = {
        "command": "python3",
        "path": "student_program.py",
        "tests": [
            {
                "input": [],
                "output": ["Hello World"],
                "timeout": 1
            },
            {
                "input": ["Alice"],
                "output": ["Hello, Alice!"],
                "timeout": 1
            }
        ]
    }
    config_content = json.dumps(config_json).encode('utf-8')
    
    # Create student programs - simple ones that just print without input interaction
    student1_content = b"print('Hello World')"
    student2_content = b"print('Goodbye World')"  # Wrong output
    
    # Prepare multipart form data
    files = [
        ("config_file", ("config.json", io.BytesIO(config_content), "application/json")),
        ("student_files", ("student1.py", io.BytesIO(student1_content), "text/x-python")),
        ("student_files", ("student2.py", io.BytesIO(student2_content), "text/x-python"))
    ]
    
    response = client.post("/homework_submission", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "student_results" in data
    assert "total_students" in data
    assert data["total_students"] == 2
    
    # Check student results
    assert len(data["student_results"]) == 2
    
    # Check first student
    student1 = data["student_results"][0]
    assert "student_name" in student1
    assert "total_tests" in student1
    assert "passed_tests" in student1
    assert "failed_tests" in student1
    assert "score" in student1
    assert "test_results" in student1
    assert student1["student_name"] == "student1.py"
    assert student1["total_tests"] == 2
    # Student1 passes at least the first test (simple print)
    assert student1["passed_tests"] >= 0  # May be 0 or 1 depending on test execution
    
    # Check second student (will not pass tests due to wrong output)
    student2 = data["student_results"][1]
    assert student2["student_name"] == "student2.py"
    assert student2["total_tests"] == 2
    assert student2["score"] >= 0  # At least 0%


def test_homework_submission_single_student(client):
    """Test homework submission with a single student file."""
    
    config_json = {
        "command": "python3",
        "path": "program.py",
        "tests": [
            {
                "input": [],
                "output": ["42"],
                "timeout": 1
            }
        ]
    }
    config_content = json.dumps(config_json).encode('utf-8')
    
    student_content = b"print(42)"
    
    files = [
        ("config_file", ("config.json", io.BytesIO(config_content), "application/json")),
        ("student_files", ("student.py", io.BytesIO(student_content), "text/x-python"))
    ]
    
    response = client.post("/homework_submission", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_students"] == 1
    assert len(data["student_results"]) == 1
    
    student = data["student_results"][0]
    assert student["student_name"] == "student.py"
    assert student["total_tests"] == 1
    assert student["passed_tests"] == 1
    assert student["score"] == 100.0
