import json
from dataclasses import asdict

import pytest

from src.apps.server.main import app, global_config
from src.core.config_parser.data import TestSuiteConfig, TestData
from src.core.execution.data import ExecutionManagerInputData


@pytest.fixture
def client():
    global_config.execution_manager_data = {
        "program.out": [
            ExecutionManagerInputData(
                command='python3 "program.out"',
                input=[],
                output=["Hello World"],
                timeout=1,
            )
        ]
    }
    app.testing = True
    with app.test_client() as client:
        yield client


def test_index_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200


def test_update_test_suite_endpoint(client):
    test_data = TestSuiteConfig(
        command="python3",
        path="program.py",
        tests=[TestData(input=[], output=["xz"], timeout=1)],
    )
    response = client.post(
        "/update_test_suite",
        data=json.dumps(asdict(test_data)),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.get_json() == {"message": "Tests updated successfully"}


def test_execute_endpoint(client):
    script_text = "print('Hello World')"

    data = {"script_text": script_text}
    response = client.post(
        "/execute_tests",
        data=json.dumps(data),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "results": [
            {
                "name": "program.out",
                "passed_tests_ratio": 100.0,
                "tests": [
                    {
                        "error": "",
                        "expected_output": "Hello World",
                        "input": "",
                        "output": "Hello World",
                        "result": "ComparisonResult.MATCH",
                    }
                ],
            }
        ],
        "total_passed_tests": 1,
        "total_tests": 1,
    }
