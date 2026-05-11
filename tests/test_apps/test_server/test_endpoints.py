import sys

sys.path.append(".")

import tempfile
from dataclasses import asdict
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.apps.server.database.configuration_data import update_execution_manager_data
from src.apps.server.app.testio_server import app
from src.apps.server.routes.execute_tests import process_file_for_server
from src.core.config_parser.data import TestData, TestSuiteConfig
from src.core.execution.data import ExecutionManagerInputData


@pytest.fixture
def client():
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
        json=asdict(test_data),
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Tests updated successfully"}


def test_execute_endpoint(client):
    script_text = "print('Hello World')"

    data = {"script_text": script_text}
    response = client.post(
        "/execute_tests",
        json=data,
    )

    assert response.status_code == 200
    assert response.json() == {
        "results": [
            {
                "name": "program.py",
                "passed_tests_ratio": 100.0,
                "tests": [
                    {
                        "error": "",
                        "expected_output": "Hello World",
                        "input": "",
                        "output": "Hello World",
                        "result_name": "MATCH",
                        "result": "ComparisonResult.MATCH",
                    }
                ],
            }
        ],
        "total_passed_tests": 1,
        "total_tests": 1,
    }


def test_process_file_for_server_does_not_overwrite_source_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        original_path = Path(temp_dir) / "program.py"
        original_path.write_text("print('original')", encoding="utf-8")

        file_path, results, num_tests, passed_tests, ratio = process_file_for_server(
            (
                str(original_path),
                "print('submitted')",
                [
                    ExecutionManagerInputData(
                        command=f'python3 "{original_path}"',
                        input=[],
                        output=["submitted"],
                        timeout=5,
                    )
                ],
            )
        )

        assert file_path == str(original_path)
        assert num_tests == 1
        assert passed_tests == 1
        assert ratio == 100.0
        assert results[0].output == "submitted"
        assert original_path.read_text(encoding="utf-8") == "print('original')"
