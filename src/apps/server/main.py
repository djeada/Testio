from pathlib import Path

from flask import Flask, request, jsonify, render_template
import sys

sys.path.append(".")

import argparse
from src.core.config_parser.parsers import ConfigParser
from src.core.execution.data import ComparisonResult, ExecutionManagerFactory
from src.core.execution.manager import ExecutionManager

app = Flask(__name__)

global_config = None
PATH_TO_PROGRAM = "pogram.out"


class Parser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super(Parser, self).__init__(*args, **kwargs)
        self.add_argument(
            "config_file", type=str, help="Path to config file", nargs="?"
        )


def update_execution_manager_data(execution_manager_data):
    global global_config
    global_config = execution_manager_data


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/update_test_suite", methods=["POST"])
def api_tests():
    # Get the test data from the request body
    json_data = request.get_json()

    parser = ConfigParser()
    test_suite_config = parser.parse_from_json(json_data)

    # Update the execution manager data
    execution_manager_data = ExecutionManagerFactory.from_test_suite_config_server(
        test_suite_config, PATH_TO_PROGRAM
    )
    update_execution_manager_data(execution_manager_data)

    # Return a success message
    return {"message": "Tests updated successfully"}, 200


@app.route("/execute", methods=["POST"])
def execute():
    # Get the script text from the request body
    global global_config
    execution_manager_data = global_config

    script_text = request.form["script_text"]

    # create a file in PATH_TO_PROGRAM and write script_text to it
    Path(PATH_TO_PROGRAM).write_text(script_text)
    manager = ExecutionManager()

    # Initialize the result list and the passed test count
    results = []
    passed_test_count = 0

    # Iterate through the execution_manager_data and run the tests
    for data in execution_manager_data:
        result = manager.run(data)
        results.append(result)

        # If the test passed, increase the passed test count
        if result.result == ComparisonResult.MATCH:
            passed_test_count += 1

    # Calculate the passed tests ratio
    total_test = len(results)
    passed_tests_ratio = passed_test_count / total_test * 100

    # Return the results in JSON format, results are list of ComparisonOutputData objects which can be transformed to dict
    return jsonify(
        {
            "results": [result.to_dict() for result in results],
            "passed_tests_ratio": passed_tests_ratio,
        }
    )


def main(argv: list = ()):

    argument_parser = Parser()
    args = argument_parser.parse_args(argv)
    # check if config file is provided
    if args.config_file:
        path = args.config_file
        parser = ConfigParser()
        test_suite_config = parser.parse_from_path(path)
        execution_manager_data = ExecutionManagerFactory.from_test_suite_config_server(
            test_suite_config, PATH_TO_PROGRAM
        )
        update_execution_manager_data(execution_manager_data)

    app.run()


if __name__ == "__main__":
    argv = sys.argv[1]
    # if argv is not list make it list
    if not isinstance(argv, list):
        argv = [argv]
    main(argv)
