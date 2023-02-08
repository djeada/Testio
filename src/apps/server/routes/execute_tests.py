import sys

sys.path.append(".")

from pathlib import Path

from flask import Blueprint, jsonify, request

from src.apps.server.database.configuration_data import global_config
from src.core.execution.data import ComparisonResult
from src.core.execution.manager import ExecutionManager

execute_tests_blueprint = Blueprint("execute_tests", __name__)


@execute_tests_blueprint.route("/execute_tests", methods=["POST"])
def execute_tests():
    execution_manager_data = global_config.execution_manager_data

    # create a file in PATH_TO_PROGRAM and write script_text to it.
    script_text = request.json["script_text"]
    manager = ExecutionManager()

    # Initialize the result list and the passed test count
    json_response = {"total_tests": 0, "total_passed_tests": 0, "results": []}

    # Iterate through the execution_manager_data and run the tests
    for path, execution_manager_data in execution_manager_data.items():
        print(path)
        Path(path).write_text(script_text)

        test_num = 1
        results = []

        for data in execution_manager_data:
            result = manager.run(data)
            results.append(result)
            json_response["total_tests"] += 1
            if result.result == ComparisonResult.MATCH:
                json_response["total_passed_tests"] += 1
            test_num += 1

        num_tests = len(results)
        passed_tests = len(
            [result for result in results if result.result == ComparisonResult.MATCH]
        )
        ratio = passed_tests / num_tests * 100
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
