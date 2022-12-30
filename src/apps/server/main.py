from flask import Flask, request, jsonify, render_template

from src.core.config_parser.parsers import ConfigParser
from src.core.execution.data import ComparisonResult, ExecutionManagerFactory
from src.core.execution.manager import ExecutionManager

app = Flask(__name__)

global_config = None


def update_tests(test_suite_config):
    global global_config
    global_config = test_suite_config


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/update_test_suite", methods=["POST"])
def api_tests():
    # Get the test data from the request body
    json_data = request.get_json()

    parser = ConfigParser()
    test_suite_config = parser.parse_from_json(json_data)

    # Update the tests
    update_tests(test_suite_config)

    # Return a success message
    return {"message": "Tests updated successfully"}, 200


@app.route("/execute", methods=["POST"])
def execute():
    # Get the script text from the request body
    global global_config
    test_suite_config = global_config

    script_text = request.get_data()
    manager = ExecutionManager()

    # Create a list of ExecutionManagerInputData objects from the script text
    # and the test_suite_config object
    execution_manager_data = ExecutionManagerFactory.from_test_suite_config(
        test_suite_config, ""
    )

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

    # Return the results in JSON format
    return {"results": results}, 200


def main(argv: list = ()):
    app.run()


if __name__ == "__main__":
    main()
