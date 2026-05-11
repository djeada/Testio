"""Route for immediate student code execution against a test suite (self-service exercise mode)."""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from src.apps.server.database.exam_sessions import ExamSessionsTable
from src.apps.server.settings import get_max_upload_size_mb
from src.core.config_parser.parsers import ConfigParser
from src.core.execution.command_utils import infer_source_suffix
from src.core.execution.data import ExecutionManagerFactory
from src.core.execution.queue import ExecutionPriority, get_execution_queue
from src.core.execution.result_utils import result_passed
from src.core.execution.task_runner import run_single_test

exercise_router: APIRouter = APIRouter(tags=["Exercise"])


class ExerciseSubmissionResponse(BaseModel):
    """Response model for immediate exercise submission with test results."""

    submission_id: int
    student_name: str
    total_tests: int
    passed_tests: int
    score: float
    test_results: List[Dict[str, Any]]
    submitted_at: str


def _check_size(content: bytes, label: str) -> None:
    """Raise HTTP 413 if *content* exceeds the configured upload limit."""
    max_mb = get_max_upload_size_mb()
    if max_mb > 0 and len(content) > max_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"{label} exceeds the maximum allowed size of {max_mb} MB",
        )


@exercise_router.post("/api/exercise/submit", response_model=ExerciseSubmissionResponse)
async def submit_exercise(
    student_name: str = Form(..., description="Student name or identifier"),
    code_file: UploadFile = File(..., description="Student source code file"),
    config_file: UploadFile = File(..., description="Exercise configuration JSON"),
) -> ExerciseSubmissionResponse:
    """
    Submit code for immediate execution against an exercise test suite.

    The code is executed against the provided configuration, results are
    returned immediately, and the submission (including results) is stored
    in the database for later retrieval.

    :param student_name: Student name or identifier
    :param code_file: Source code file to test
    :param config_file: Exercise configuration in JSON format
    :return: Per-test results, summary stats, and a persistent submission ID
    """
    # Validate and read the config file
    if config_file.content_type and "json" not in config_file.content_type:
        raise HTTPException(status_code=400, detail="config_file must be a JSON file")
    config_content = await config_file.read()
    _check_size(config_content, "config_file")

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

    # Read the student code file
    code_content = await code_file.read()
    _check_size(code_content, "code_file")

    suffix = infer_source_suffix(
        filename=code_file.filename or "",
        command=test_suite_config.run_command or test_suite_config.command,
        compile_command=test_suite_config.compile_command,
        path=test_suite_config.path,
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as tmp:
        tmp.write(code_content.decode("utf-8"))
        tmp_path = tmp.name

    try:
        execution_data = ExecutionManagerFactory.create_execution_manager_data(
            test_suite_config, tmp_path
        )
        queue = get_execution_queue()
        test_results = []
        for data in execution_data:
            result = await queue.submit_async(
                run_single_test, data, priority=ExecutionPriority.NORMAL
            )
            test_results.append(result.to_dict())
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    total = len(test_results)
    passed = sum(1 for r in test_results if result_passed(r))
    score = round((passed / total * 100) if total > 0 else 0.0, 2)

    db = ExamSessionsTable()
    try:
        submission_id = db.store_exercise_submission(
            student_name=student_name,
            problem_description=None,
            code=code_content.decode("utf-8"),
            additional_files=None,
            test_results=test_results,
            score=score,
        )
    finally:
        db.close()

    if submission_id is None:
        raise HTTPException(status_code=500, detail="Failed to store submission")

    return ExerciseSubmissionResponse(
        submission_id=submission_id,
        student_name=student_name,
        total_tests=total,
        passed_tests=passed,
        score=score,
        test_results=test_results,
        submitted_at=datetime.now().isoformat(),
    )
