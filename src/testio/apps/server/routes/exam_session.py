"""FastAPI routes for exam session management.

Student-facing endpoints never return a session's config, expected outputs,
test inputs or program output: a program can echo its stdin, so returning
its output would leak the test inputs as well. Students only see pass/fail
per test (and compiler errors for their own code).

To stop students submitting under someone else's ID, a student first
*joins* the session (``POST /api/exam/join``), which claims the student ID
and returns a secret token; the final submission must carry that token.
"""

import secrets
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from testio.apps.server.auth import require_teacher_auth
from testio.apps.server.database.exam_sessions import (
    DuplicateSubmissionError,
    ExamSessionsTable,
)
from testio.apps.server.execution import SubmissionRun, run_submission
from testio.apps.server.uploads import parse_config_or_400
from testio.apps.server.validation import (
    MAX_CODE_CHARS,
    validate_session_id,
    validate_student_id,
)
from testio.core.config_parser.data import TestSuiteConfig
from testio.core.config_parser.parsers import ConfigNotParsable, ConfigParser
from testio.core.execution.queue import ExecutionPriority

exam_session_router = APIRouter()


class CreateSessionRequest(BaseModel):
    """Request model for creating an exam session."""

    config_data: Dict[str, Any]


class CreateSessionResponse(BaseModel):
    """Response model for creating an exam session."""

    session_id: str
    session_url: str


class _StudentRequest(BaseModel):
    session_id: str
    student_id: str

    @field_validator("session_id")
    @classmethod
    def _check_session_id(cls, value: str) -> str:
        return validate_session_id(value)

    @field_validator("student_id")
    @classmethod
    def _check_student_id(cls, value: str) -> str:
        return validate_student_id(value)


class JoinSessionRequest(_StudentRequest):
    """Request model for joining an exam session."""


class JoinSessionResponse(BaseModel):
    """Token authorising the student's final submission."""

    session_id: str
    student_id: str
    student_token: str


class TestCodeRequest(_StudentRequest):
    """Request model for testing student code."""

    code: str = Field(..., min_length=1, max_length=MAX_CODE_CHARS)
    student_token: Optional[str] = Field(default=None, max_length=200)


class TestCodeResponse(BaseModel):
    """Response model for testing student code."""

    test_results: List[Dict[str, Any]]
    total_tests: int
    passed_tests: int
    score: float
    compile_error: Optional[str] = None


class SubmitCodeRequest(_StudentRequest):
    """Request model for submitting student code."""

    code: str = Field(..., min_length=1, max_length=MAX_CODE_CHARS)
    student_token: str = Field(..., min_length=1, max_length=200)


class SubmitCodeResponse(BaseModel):
    """Response model for code submission."""

    success: bool
    message: str
    test_results: Optional[List[Dict[str, Any]]] = None
    total_tests: Optional[int] = None
    passed_tests: Optional[int] = None
    score: Optional[float] = None
    compile_error: Optional[str] = None


class SessionSubmissionsResponse(BaseModel):
    """Response model for session submissions."""

    session_id: str
    total_submissions: int
    submissions: List[Dict[str, Any]]


class PublicSessionResponse(BaseModel):
    """What a student may know about a session (no tests, no answers)."""

    session_id: str
    is_active: bool
    created_at: str
    closed_at: Optional[str] = None
    total_tests: int


def _student_view(run: SubmissionRun) -> List[Dict[str, Any]]:
    """Per-test pass/fail only; no inputs, expected or actual output."""
    return [
        {"test": index, "result_name": r["result_name"], "result": r["result"]}
        for index, r in enumerate(run.test_results, start=1)
    ]


def _get_active_session(exam_db: ExamSessionsTable, session_id: str) -> Dict[str, Any]:
    session = exam_db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session["is_active"]:
        raise HTTPException(status_code=403, detail="Session is no longer active")
    return session


def _session_suite(session: Dict[str, Any]) -> TestSuiteConfig:
    try:
        return ConfigParser().parse_from_json(session["config_data"])
    except ConfigNotParsable:
        raise HTTPException(
            status_code=409, detail="This exam's test configuration is invalid"
        )


@exam_session_router.post(
    "/api/exam/create_session", response_model=CreateSessionResponse
)
async def create_exam_session(
    request: CreateSessionRequest,
    _auth: None = Depends(require_teacher_auth),
) -> CreateSessionResponse:
    """
    Create a new exam session with the given configuration.

    :param request: Configuration data for the exam
    :return: Session ID and URL for students
    """
    parse_config_or_400(request.config_data)

    # Unguessable: the ID is the only thing a student needs to open the exam.
    session_id = secrets.token_urlsafe(16)

    exam_db = ExamSessionsTable()
    try:
        success = exam_db.create_session(session_id, request.config_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create session")

        session_url = f"/student/{session_id}"
        return CreateSessionResponse(session_id=session_id, session_url=session_url)
    finally:
        exam_db.close()


@exam_session_router.get("/api/exam/session/{session_id}")
async def get_exam_session(
    session_id: str,
    _auth: None = Depends(require_teacher_auth),
) -> Dict[str, Any]:
    """
    Get full exam session details, including the config (teacher only).

    :param session_id: The session ID
    :return: Session data
    """
    exam_db = ExamSessionsTable()
    try:
        session = exam_db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    finally:
        exam_db.close()


@exam_session_router.get(
    "/api/exam/session/{session_id}/public", response_model=PublicSessionResponse
)
async def get_public_exam_session(session_id: str) -> PublicSessionResponse:
    """
    Student-safe session information: status and number of tests only.

    :param session_id: The session ID
    """
    exam_db = ExamSessionsTable()
    try:
        session = exam_db.get_session(session_id)
    finally:
        exam_db.close()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    tests = session["config_data"].get("tests") or []
    return PublicSessionResponse(
        session_id=session["session_id"],
        is_active=session["is_active"],
        created_at=session["created_at"],
        closed_at=session["closed_at"],
        total_tests=len(tests) if isinstance(tests, list) else 0,
    )


@exam_session_router.post("/api/exam/join", response_model=JoinSessionResponse)
async def join_exam_session(request: JoinSessionRequest) -> JoinSessionResponse:
    """
    Claim a student ID in an exam session.

    Returns a token that must accompany the final submission. Each student ID
    can be claimed once; the teacher can release a claim with
    ``DELETE /api/exam/session/{session_id}/participants/{student_id}``.
    """
    exam_db = ExamSessionsTable()
    try:
        _get_active_session(exam_db, request.session_id)
        token = exam_db.register_participant(request.session_id, request.student_id)
    finally:
        exam_db.close()
    if token is None:
        raise HTTPException(
            status_code=409,
            detail="This student ID has already joined this exam. If this is "
            "your ID, use the browser you joined with or ask your teacher to "
            "reset it.",
        )
    return JoinSessionResponse(
        session_id=request.session_id,
        student_id=request.student_id,
        student_token=token,
    )


@exam_session_router.post("/api/exam/test_code", response_model=TestCodeResponse)
async def test_student_code(request: TestCodeRequest) -> TestCodeResponse:
    """
    Test student code without submitting it (for practice).

    Only pass/fail per test is returned, never expected outputs or inputs.

    :param request: Student code and session information
    :return: Test results
    """
    exam_db = ExamSessionsTable()
    try:
        session = _get_active_session(exam_db, request.session_id)
    finally:
        exam_db.close()

    run = await run_submission(
        _session_suite(session), request.code, priority=ExecutionPriority.HIGH
    )
    return TestCodeResponse(
        test_results=_student_view(run),
        total_tests=run.total_tests,
        passed_tests=run.passed_tests,
        score=run.score,
        compile_error=run.compile_error or None,
    )


@exam_session_router.post("/api/exam/submit_code", response_model=SubmitCodeResponse)
async def submit_student_code(request: SubmitCodeRequest) -> SubmitCodeResponse:
    """
    Submit student code for final grading.

    Requires the ``student_token`` returned by ``/api/exam/join``. A student
    can submit once; concurrent duplicates are rejected atomically.

    :param request: Student code and session information
    :return: Submission confirmation with (pass/fail) test results
    """
    exam_db = ExamSessionsTable()
    try:
        session = _get_active_session(exam_db, request.session_id)
        if not exam_db.verify_participant(
            request.session_id, request.student_id, request.student_token
        ):
            raise HTTPException(
                status_code=403,
                detail="Invalid student token for this student ID. Join the exam "
                "first, from the browser you will submit with.",
            )
        # Cheap early exit; the INSERT below is what actually enforces it.
        if exam_db.get_student_submission(request.session_id, request.student_id):
            raise HTTPException(
                status_code=409,
                detail="You have already submitted your work for this exam",
            )

        run = await run_submission(
            _session_suite(session), request.code, priority=ExecutionPriority.NORMAL
        )

        try:
            stored = exam_db.submit_student_work(
                request.session_id,
                request.student_id,
                request.code,
                run.test_results,
                run.score,
            )
        except DuplicateSubmissionError:
            raise HTTPException(
                status_code=409,
                detail="You have already submitted your work for this exam",
            )
        if not stored:
            raise HTTPException(status_code=500, detail="Failed to store submission")

        return SubmitCodeResponse(
            success=True,
            message="Code submitted successfully",
            test_results=_student_view(run),
            total_tests=run.total_tests,
            passed_tests=run.passed_tests,
            score=run.score,
            compile_error=run.compile_error or None,
        )
    finally:
        exam_db.close()


@exam_session_router.get(
    "/api/exam/submissions/{session_id}", response_model=SessionSubmissionsResponse
)
async def get_session_submissions(
    session_id: str,
    _auth: None = Depends(require_teacher_auth),
) -> SessionSubmissionsResponse:
    """
    Get all submissions for an exam session (teacher view).

    :param session_id: The session ID
    :return: All student submissions with results
    """
    exam_db = ExamSessionsTable()
    try:
        session = exam_db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        submissions = exam_db.get_session_submissions(session_id)

        return SessionSubmissionsResponse(
            session_id=session_id,
            total_submissions=len(submissions),
            submissions=submissions,
        )
    finally:
        exam_db.close()


@exam_session_router.post("/api/exam/end_session/{session_id}")
async def end_exam_session(
    session_id: str,
    _auth: None = Depends(require_teacher_auth),
) -> Dict[str, str]:
    """
    End an exam session (no more submissions allowed).

    :param session_id: The session ID to end
    :return: Success message
    :raises HTTPException 404: if the session does not exist
    """
    exam_db = ExamSessionsTable()
    try:
        if not exam_db.end_session(session_id):
            raise HTTPException(status_code=404, detail="Session not found")
        return {"message": "Session ended successfully"}
    finally:
        exam_db.close()


@exam_session_router.delete("/api/exam/session/{session_id}/participants/{student_id}")
async def release_exam_participant(
    session_id: str,
    student_id: str,
    _auth: None = Depends(require_teacher_auth),
) -> Dict[str, str]:
    """
    Release a claimed student ID so the student can join again (e.g. after
    switching computers, or if someone else claimed their ID).
    """
    exam_db = ExamSessionsTable()
    try:
        if not exam_db.remove_participant(session_id, student_id):
            raise HTTPException(status_code=404, detail="Participant not found")
        return {"message": "Participant released"}
    finally:
        exam_db.close()


@exam_session_router.delete("/api/exam/session/{session_id}")
async def delete_exam_session(
    session_id: str,
    _auth: None = Depends(require_teacher_auth),
) -> Dict[str, str]:
    """
    Soft-delete an exam session and its submissions (GDPR-style cleanup).

    The session is marked as deleted and will no longer appear in any
    listing or export endpoint, but data is retained in the database.

    :param session_id: The session ID to delete
    :return: Confirmation message
    """
    exam_db = ExamSessionsTable()
    try:
        found = exam_db.delete_session(session_id)
        if not found:
            raise HTTPException(
                status_code=404,
                detail="Session not found or already deleted",
            )
        return {"message": "Session deleted successfully"}
    finally:
        exam_db.close()
