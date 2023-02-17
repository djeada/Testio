"""This module defines a Flask blueprint for updating the test suite configuration and execution manager data."""
import sys

sys.path.append(".")

from flask import Blueprint, request
from src.apps.server.database.configuration_data import update_execution_manager_data
from src.core.config_parser.parsers import ConfigParser
from src.core.execution.data import ExecutionManagerFactory

update_test_suite_blueprint: Blueprint = Blueprint("update_test_suite", __name__)


@update_test_suite_blueprint.route("/update_test_suite", methods=["POST"])
def update_test_suite() -> tuple:
    """Updates the test suite configuration and execution manager data with the provided test data.

    Returns:
        tuple: A tuple containing a success message and status code.
    """
    # Parse the test data from the request body
    json_data = request.get_json()
    parser = ConfigParser()
    test_suite_config = parser.parse_from_json(json_data)

    # Update the execution manager data with the new test suite configuration
    execution_manager_data = ExecutionManagerFactory.from_test_suite_config_server(
        test_suite_config
    )
    update_execution_manager_data(execution_manager_data)

    # Return a success message and status code
    return {"message": "Tests updated successfully"}, 200
