"""This module defines a Flask blueprint for executing tests and returning the results in JSON format."""

import sys

sys.path.append(".")

from pathlib import Path
from flask import Blueprint, jsonify, request, Response
from src.core.execution.data import ComparisonResult, ComparisonOutputData
from src.core.execution.manager import ExecutionManager
from src.apps.server.database.configuration_data import parse_config_data

execute_tests_blueprint: Blueprint = Blueprint("execute_tests", __name__)


@execute_tests_blueprint.route("/execute_tests", methods=["POST"])
def execute_tests() -> Response:
    """Executes tests using the provided script text and returns the results in JSON format.

    :return: The JSON-encoded test results.
    """
    execution_manager_data = parse_config_data()

    # create a file in PATH_TO_PROGRAM and write script_text to it.
    script_text: str = request.json["script_text"]
    manager: ExecutionManager = ExecutionManager()

    # Initialize the result list and the passed test count
    json_response = {"total_tests": 0, "total_passed_tests": 0, "results": []}

    # Iterate through the execution_manager_data and run the tests
    for path, execution_manager_data in execution_manager_data.items():
        Path(path).write_text(script_text)

        test_num: int = 1
        results: list[ComparisonOutputData] = []

        for data in execution_manager_data:
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
    return jsonify(json_response)
