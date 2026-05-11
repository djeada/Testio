"""This module defines a FastAPI router for handling homework submissions with multiple student programs."""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from src.apps.server.settings import get_max_upload_size_mb
from src.core.config_parser.parsers import ConfigParser
from src.core.execution.command_utils import infer_source_suffix
from src.core.execution.data import ExecutionManagerFactory
from src.core.execution.manager import ExecutionManager
from src.core.execution.result_utils import result_passed

homework_submission_router: APIRouter = APIRouter()


class HomeworkSubmissionResponse(BaseModel):
    """Response model for homework submission endpoint."""

    student_results: List[Dict[str, Any]]
    total_students: int


def _enforce_upload_limit(content: bytes, label: str) -> None:
    """Raise HTTP 413 if *content* exceeds TESTIO_MAX_UPLOAD_SIZE_MB."""
    max_mb = get_max_upload_size_mb()
    if max_mb > 0 and len(content) > max_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"{label} exceeds the maximum allowed upload size of {max_mb} MB",
        )


@homework_submission_router.post(
    "/homework_submission", response_model=HomeworkSubmissionResponse
)
async def homework_submission(
    config_file: UploadFile = File(..., description="Configuration JSON file"),
    student_files: List[UploadFile] = File(
        ..., description="List of student program files"
    ),
) -> HomeworkSubmissionResponse:
    """
    Test multiple student programs against a configuration file.

    :param config_file: The configuration JSON file containing test specifications
    :param student_files: List of student program files to test
    :return: Test results for each student program
    """
    # Validate config_file content-type
    if config_file.content_type and "json" not in config_file.content_type:
        raise HTTPException(
            status_code=400,
            detail="config_file must be a JSON file (content-type: application/json)",
        )

    # Read and validate config file size
    config_content = await config_file.read()
    _enforce_upload_limit(config_content, "config_file")

    try:
        config_json = json.loads(config_content.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="config_file contains invalid JSON")

    parser = ConfigParser()
    try:
        test_suite_config = parser.parse_from_json(config_json)
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Invalid test configuration: {exc}"
        )

    # Initialize execution manager
    manager = ExecutionManager()

    # Store results for all students
    student_results = []

    # Process each student file
    for student_file in student_files:
        student_content = await student_file.read()
        _enforce_upload_limit(
            student_content, f"student file '{student_file.filename}'"
        )

        suffix = infer_source_suffix(
            filename=student_file.filename or "",
            command=test_suite_config.run_command or test_suite_config.command,
            compile_command=test_suite_config.compile_command,
            path=test_suite_config.path,
        )

        # Create a temporary file for the student's program
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, delete=False
        ) as temp_file:
            temp_file.write(student_content.decode("utf-8"))
            temp_file_path = temp_file.name

        try:
            # Create execution manager data for this student's program
            execution_manager_data = (
                ExecutionManagerFactory.create_execution_manager_data(
                    test_suite_config, temp_file_path
                )
            )

            # Run all tests for this student
            test_results = []
            for data in execution_manager_data:
                result = manager.run(data)
                test_results.append(result.to_dict())

            # Calculate statistics
            total_tests = len(test_results)
            passed_tests = len([r for r in test_results if result_passed(r)])
            score = (passed_tests / total_tests * 100) if total_tests > 0 else 0

            student_results.append(
                {
                    "student_name": student_file.filename,
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": total_tests - passed_tests,
                    "score": round(score, 2),
                    "test_results": test_results,
                }
            )
        finally:
            # Clean up temporary file
            Path(temp_file_path).unlink(missing_ok=True)

    return HomeworkSubmissionResponse(
        student_results=student_results, total_students=len(student_files)
    )
