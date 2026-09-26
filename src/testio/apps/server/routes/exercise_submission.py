"""Route for immediate code execution against an uploaded exercise config.

The caller supplies the config - and with it the commands that are executed
on the server - so this is a teacher-only operation (for example, a teacher
or an LMS integration submitting on a student's behalf). Students practise
through ``/execute_tests`` (the teacher-loaded suite) or exam sessions, which
never accept a config from the client.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from testio.apps.server.auth import require_teacher_auth
from testio.apps.server.database.exam_sessions import ExamSessionsTable
from testio.apps.server.execution import run_submission
from testio.apps.server.uploads import read_config_upload, read_upload_capped
from testio.core.execution.queue import ExecutionPriority

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


@exercise_router.post("/api/exercise/submit", response_model=ExerciseSubmissionResponse)
async def submit_exercise(
    student_name: str = Form(
        ..., min_length=1, max_length=200, description="Student name or identifier"
    ),
    code_file: UploadFile = File(..., description="Student source code file"),
    config_file: UploadFile = File(..., description="Exercise configuration JSON"),
    _auth: None = Depends(require_teacher_auth),
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
    test_suite_config = await read_config_upload(config_file)
    code_content = await read_upload_capped(code_file, "code_file")

    run = await run_submission(
        test_suite_config,
        code_content,
        filename=Path(code_file.filename or "").name,
        priority=ExecutionPriority.NORMAL,
    )

    db = ExamSessionsTable()
    try:
        submission_id = db.store_exercise_submission(
            student_name=student_name,
            problem_description=None,
            code=code_content.decode("utf-8", errors="replace"),
            additional_files=None,
            test_results=run.test_results,
            score=run.score,
        )
    finally:
        db.close()

    if submission_id is None:
        raise HTTPException(status_code=500, detail="Failed to store submission")

    return ExerciseSubmissionResponse(
        submission_id=submission_id,
        student_name=student_name,
        total_tests=run.total_tests,
        passed_tests=run.passed_tests,
        score=run.score,
        test_results=run.test_results,
        submitted_at=datetime.now().isoformat(),
    )
