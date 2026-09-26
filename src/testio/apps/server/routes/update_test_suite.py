"""This module defines a FastAPI router for updating the test suite configuration and execution manager data."""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from testio.apps.server.auth import require_teacher_auth
from testio.apps.server.database.configuration_data import (
    update_execution_manager_data,
    update_suite_config,
)
from testio.apps.server.uploads import parse_config_or_400
from testio.core.execution.data import ExecutionManagerFactory

logger = logging.getLogger(__name__)

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
    test_suite_config = parse_config_or_400(json_data)

    try:
        execution_manager_data = ExecutionManagerFactory.from_test_suite_config_server(
            test_suite_config
        )
    except Exception:
        logger.exception("Failed to build execution manager data")
        raise HTTPException(
            status_code=400, detail="Failed to build execution manager data"
        )

    try:
        # The raw config is what /execute_tests runs submissions against
        # (it keeps compile_command); the per-file data is kept for
        # backward compatibility.
        update_suite_config(json_data)
        update_execution_manager_data(execution_manager_data)
    except Exception:
        logger.exception("Failed to persist test suite data")
        raise HTTPException(status_code=500, detail="Failed to persist test suite data")

    return {"message": "Tests updated successfully"}
