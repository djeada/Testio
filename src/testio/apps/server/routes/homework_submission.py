"""This module defines a FastAPI router for handling homework submissions with multiple student programs.

Homework grading is a teacher operation: the caller supplies the config (and
therefore the commands that are executed), so the endpoint requires teacher
authentication.
"""

from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel

from testio.apps.server.auth import require_teacher_auth
from testio.apps.server.execution import run_submission
from testio.apps.server.uploads import (
    enforce_file_count,
    read_config_upload,
    read_upload_capped,
)
from testio.core.execution.queue import ExecutionPriority

homework_submission_router: APIRouter = APIRouter()


class HomeworkSubmissionResponse(BaseModel):
    """Response model for homework submission endpoint."""

    student_results: List[Dict[str, Any]]
    total_students: int


@homework_submission_router.post(
    "/homework_submission", response_model=HomeworkSubmissionResponse
)
async def homework_submission(
    config_file: UploadFile = File(..., description="Configuration JSON file"),
    student_files: List[UploadFile] = File(
        ..., description="List of student program files"
    ),
    _auth: None = Depends(require_teacher_auth),
) -> HomeworkSubmissionResponse:
    """
    Test multiple student programs against a configuration file.

    Each program is compiled (when the config has a ``compile_command``) and
    run in its own temporary directory through the shared execution queue.

    :param config_file: The configuration JSON file containing test specifications
    :param student_files: List of student program files to test
    :return: Test results for each student program
    """
    enforce_file_count(student_files)
    test_suite_config = await read_config_upload(config_file)

    student_results = []
    for student_file in student_files:
        filename = Path(student_file.filename or "").name
        content = await read_upload_capped(student_file, f"student file '{filename}'")

        run = await run_submission(
            test_suite_config,
            content,
            filename=filename,
            priority=ExecutionPriority.LOW,
        )
        student_results.append(
            {
                "student_name": filename,
                "total_tests": run.total_tests,
                "passed_tests": run.passed_tests,
                "failed_tests": run.total_tests - run.passed_tests,
                "score": run.score,
                "test_results": run.test_results,
            }
        )

    return HomeworkSubmissionResponse(
        student_results=student_results, total_students=len(student_files)
    )
