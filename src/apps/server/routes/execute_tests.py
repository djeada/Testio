"""This module defines a FastAPI router for executing tests and returning the results in JSON format."""

import tempfile
from dataclasses import replace
from typing import Dict, Any, Tuple, List
from concurrent.futures import ProcessPoolExecutor

from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel
from src.core.execution.data import (
    ComparisonResult,
    ComparisonOutputData,
    ExecutionManagerInputData,
)
from src.core.execution.command_utils import infer_source_suffix, replace_command_path
from src.core.execution.manager import ExecutionManager
from src.apps.server.database.configuration_data import parse_config_data

execute_tests_router: APIRouter = APIRouter()


class ExecuteTestsRequest(BaseModel):
    """Request model for execute_tests endpoint."""

    script_text: str


def process_file_for_server(
    args: Tuple[str, str, List[ExecutionManagerInputData]],
) -> Tuple[str, List[ComparisonOutputData], int, int, float]:
    """
    Process a single file's tests and return the results.
    This function is designed to be used with ProcessPoolExecutor for the server.

    :param args: A tuple containing (path, script_text, exec_data)
    :return: A tuple containing (path, results, total_tests, passed_tests, ratio)
    """
    path, script_text, exec_data = args
    suffix = infer_source_suffix(
        path=path,
        command=exec_data[0].command if exec_data else "",
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / f"{Path(path).stem}{suffix}"
        temp_path.write_text(script_text, encoding="utf-8")

        rewritten_exec_data = [
            replace(
                data,
                command=replace_command_path(data.command, path, str(temp_path)),
            )
            for data in exec_data
        ]

        manager = ExecutionManager()
        results: List[ComparisonOutputData] = []

        for data in rewritten_exec_data:
            result = manager.run(data)
            results.append(result)

    num_tests = len(results)
    passed_tests = len(
        [result for result in results if result.result == ComparisonResult.MATCH]
    )
    ratio = (passed_tests / num_tests * 100) if num_tests > 0 else 0.0

    return path, results, num_tests, passed_tests, ratio


@execute_tests_router.post("/execute_tests")
def execute_tests(request_data: ExecuteTestsRequest) -> Dict[str, Any]:
    """Executes tests using the provided script text and returns the results in JSON format.

    :return: The JSON-encoded test results.
    """
    execution_manager_data = parse_config_data()

    script_text: str = request_data.script_text

    # Initialize the result list and the passed test count
    json_response: Dict[str, Any] = {
        "total_tests": 0,
        "total_passed_tests": 0,
        "results": [],
    }

    # Prepare arguments for parallel processing
    pool_args = [
        (path, script_text, exec_data)
        for path, exec_data in execution_manager_data.items()
    ]

    # Use ProcessPoolExecutor to run tests for multiple files concurrently
    with ProcessPoolExecutor() as executor:
        file_results = list(executor.map(process_file_for_server, pool_args))

    # Aggregate results
    for path, results, num_tests, passed_tests, ratio in file_results:
        json_response["total_tests"] += num_tests
        json_response["total_passed_tests"] += passed_tests
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
