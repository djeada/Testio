import sys

sys.path.append(".")

from flask import Blueprint, request

from src.apps.server.database.configuration_data import update_execution_manager_data
from src.core.config_parser.parsers import ConfigParser
from src.core.execution.data import ExecutionManagerFactory

update_test_suite_blueprint = Blueprint("update_test_suite", __name__)


@update_test_suite_blueprint.route("/update_test_suite", methods=["POST"])
def update_test_suite():
    # Get the test data from the request body
    json_data = request.get_json()

    parser = ConfigParser()
    test_suite_config = parser.parse_from_json(json_data)

    # Update the execution manager data
    execution_manager_data = ExecutionManagerFactory.from_test_suite_config_server(
        test_suite_config
    )
    update_execution_manager_data(execution_manager_data)

    # Return a success message
    return {"message": "Tests updated successfully"}, 200
