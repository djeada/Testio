import copy
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
PATH_TO_PROGRAM = "program.out"


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
    execution_manager_data = ExecutionManagerFactory.from_test_suite_config_server(test_suite_config)
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
    #Path(PATH_TO_PROGRAM).write_text(script_text)
    manager = ExecutionManager()

    # Initialize the result list and the passed test count
    json_response = {"total_tests": 0, "total_passed_tests": 0, "results": []}

    # Iterate through the execution_manager_data and run the tests
    for path, execution_manager_data in execution_manager_data.items():
        print(path)
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
        passed_tests = len([result for result in results if result.result == ComparisonResult.MATCH])
        ratio = passed_tests / num_tests * 100
        json_response["results"].append({"tests": [result.to_dict() for result in results],
                                         "passed_tests_ratio": ratio, "name": Path(path).name})

    # Return the results in JSON format, results are list of ComparisonOutputData objects which can be transformed to
    # dict
    return jsonify(json_response)


def main(argv: list = ()):

    argument_parser = Parser()
    args = argument_parser.parse_args(argv)
    # check if config file is provided
    if args.config_file:
        path = args.config_file
        parser = ConfigParser()
        test_suite_config = parser.parse_from_path(path)
        execution_manager_data = ExecutionManagerFactory.from_test_suite_config_server(test_suite_config)
        update_execution_manager_data(execution_manager_data)

    app.run()


if __name__ == "__main__":
    argv = sys.argv[1]
    # if argv is not list make it list
    if not isinstance(argv, list):
        argv = [argv]
    main(argv)
