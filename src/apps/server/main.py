import argparse
import dataclasses
from pathlib import Path
from flask import Flask, request, jsonify, render_template
import sys

sys.path.append(".")

from src.core.config_parser.parsers import ConfigParser
from src.core.execution.data import ComparisonResult, ExecutionManagerFactory
from src.core.execution.manager import ExecutionManager


@dataclasses.dataclass
class GlobalConfiguration:
    execution_manager_data = None


app = Flask(__name__)
global_config = GlobalConfiguration()
PATH_TO_PROGRAM = "program.out"


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_argument(
            "config_file", type=str, help="Path to config file", nargs="?"
        )


def update_execution_manager_data(execution_manager_data):
    global global_config
    global_config.execution_manager_data = execution_manager_data


@app.route("/")
def index_page():
    return render_template("index.html")


@app.route("/update_test_suite", methods=["POST"])
def update_test_suite():
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


@app.route("/execute_tests", methods=["POST"])
def execute_tests():
    global global_config
    execution_manager_data = global_config.execution_manager_data

    script_text = request.form["script_text"]

    # Write script_text to PATH_TO_PROGRAM file
    Path(PATH_TO_PROGRAM).write_text(script_text)
    manager = ExecutionManager()

    results = []
    passed_test_count = 0

    for data in execution_manager_data:
        result = manager.run(data)
        results.append(result)
        if result.result == ComparisonResult.MATCH:
            passed_test_count += 1

    total_test = len(results)
    passed_tests_ratio = passed_test_count / total_test * 100

    # Return the results in JSON format
    return jsonify(
        {
            "results": [result.to_dict() for result in results],
            "passed_tests_ratio": passed_tests_ratio,
        }
    )


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    argument_parser = ArgumentParser()
    args = argument_parser.parse_args(argv)
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
    main()
