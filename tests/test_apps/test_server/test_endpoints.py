import json
import pytest

from src.apps.server.main import app, global_config
from src.core.execution.data import ExecutionManagerInputData


@pytest.fixture
def client():
    global_config.execution_manager_data = [
        ExecutionManagerInputData(
            command='python3 "program.out"', input=[], output=["Hello World"], timeout=1
        )
    ]

    app.testing = True
    with app.test_client() as client:
        yield client


def test_index_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200


def test_update_test_suite_endpoint(client):
    test_data = {"test_suite_config": {"test_case": "test_case_data"}}
    response = client.post(
        "/update_test_suite",
        data=json.dumps(test_data),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.get_json() == {"message": "Tests updated successfully"}


def test_execute_endpoint(client):
    script_text = "print('Hello World')"

    data = {"script_text": script_text}
    response = client.post(
        "/execute_tests",
        data=data,
        content_type="application/x-www-form-urlencoded",
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "passed_tests_ratio": 100.0,
        "results": [
            {
                "error": "",
                "expected_output": "Hello World",
                "input": "",
                "output": "Hello World",
                "result": "ComparisonResult.MATCH",
            }
        ],
    }
