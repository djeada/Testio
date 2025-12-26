"""This module defines a FastAPI router for executing tests and returning the results in JSON format."""

import sys
from typing import Dict, Any

sys.path.append(".")

from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel
from src.core.execution.data import ComparisonResult, ComparisonOutputData
from src.core.execution.manager import ExecutionManager
from src.apps.server.database.configuration_data import parse_config_data

execute_tests_router: APIRouter = APIRouter()


class ExecuteTestsRequest(BaseModel):
    """Request model for execute_tests endpoint."""
    script_text: str


@execute_tests_router.post("/execute_tests")
def execute_tests(request_data: ExecuteTestsRequest) -> Dict[str, Any]:
    """Executes tests using the provided script text and returns the results in JSON format.

    :return: The JSON-encoded test results.
    """
    execution_manager_data = parse_config_data()

    # create a file in PATH_TO_PROGRAM and write script_text to it.
    script_text: str = request_data.script_text
    manager: ExecutionManager = ExecutionManager()

    # Initialize the result list and the passed test count
    json_response: Dict[str, Any] = {"total_tests": 0, "total_passed_tests": 0, "results": []}

    # Iterate through the execution_manager_data and run the tests
    for path, exec_data in execution_manager_data.items():
        Path(path).write_text(script_text)

        test_num: int = 1
        results: list[ComparisonOutputData] = []

        for data in exec_data:
            result: ComparisonOutputData = manager.run(data)
            results.append(result)
            json_response["total_tests"] += 1
            if result.result == ComparisonResult.MATCH:
                json_response["total_passed_tests"] += 1
            test_num += 1

        num_tests: int = len(results)
        passed_tests: int = len(
            [result for result in results if result.result == ComparisonResult.MATCH]
        )
        ratio: float = passed_tests / num_tests * 100
        json_response["results"].append(
            {
                "tests": [result.to_dict() for result in results],
                "passed_tests_ratio": ratio,
                "name": Path(path).name,
            }
        )

    # Return the results in JSON format, results are list of ComparisonOutputData objects which can be transformed to
    # dict
    return json_response
