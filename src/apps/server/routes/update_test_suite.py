"""This module defines a FastAPI router for updating the test suite configuration and execution manager data."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from src.apps.server.auth import require_teacher_auth
from src.apps.server.database.configuration_data import update_execution_manager_data
from src.core.config_parser.parsers import ConfigParser
from src.core.execution.data import ExecutionManagerFactory

update_test_suite_router: APIRouter = APIRouter()


@update_test_suite_router.post("/update_test_suite")
def update_test_suite(
    json_data: Dict[str, Any],
    _auth: None = Depends(require_teacher_auth),
) -> Dict[str, str]:
    """Update the test suite configuration and execution manager data.

    :param json_data: Raw configuration dict (must match test-suite schema)
    :return: Success message
    :raises HTTPException 400: If the config is invalid or referenced paths don't exist
    :raises HTTPException 500: If the database update fails
    """
    parser = ConfigParser()
    try:
        test_suite_config = parser.parse_from_json(json_data)
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Invalid test suite configuration: {exc}"
        )

    try:
        execution_manager_data = ExecutionManagerFactory.from_test_suite_config_server(
            test_suite_config
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Failed to build execution manager data: {exc}"
        )

    try:
        update_execution_manager_data(execution_manager_data)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to persist test suite data: {exc}"
        )

    return {"message": "Tests updated successfully"}
