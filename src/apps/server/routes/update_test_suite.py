"""This module defines a FastAPI router for updating the test suite configuration and execution manager data."""
import sys
from typing import Dict, Any

sys.path.append(".")

from fastapi import APIRouter
from src.apps.server.database.configuration_data import update_execution_manager_data
from src.core.config_parser.parsers import ConfigParser
from src.core.execution.data import ExecutionManagerFactory

update_test_suite_router: APIRouter = APIRouter()


@update_test_suite_router.post("/update_test_suite")
def update_test_suite(json_data: Dict[str, Any]) -> Dict[str, str]:
    """Updates the test suite configuration and execution manager data with the provided test data.

    Returns:
        dict: A dictionary containing a success message.
    """
    # Parse the test data from the request body
    parser = ConfigParser()
    test_suite_config = parser.parse_from_json(json_data)

    # Update the execution manager data with the new test suite configuration
    execution_manager_data = ExecutionManagerFactory.from_test_suite_config_server(
        test_suite_config
    )
    update_execution_manager_data(execution_manager_data)

    # Return a success message
    return {"message": "Tests updated successfully"}
