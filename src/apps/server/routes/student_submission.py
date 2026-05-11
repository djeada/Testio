"""Routes for student code submissions (non-exam, self-service / teacher-review flow)."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.apps.server.database.exam_sessions import ExamSessionsTable

student_submission_router: APIRouter = APIRouter(tags=["Student Submissions"])


class AdditionalFile(BaseModel):
    """A named code file attached alongside the primary submission."""

    name: str
    content: str


class StudentSubmissionRequest(BaseModel):
    """Request model for student submission endpoint."""

    student_name: str
    problem_description: str
    code: str
    additional_files: List[AdditionalFile] = []


class StudentSubmissionResponse(BaseModel):
    """Response model for student submission endpoint."""

    success: bool
    message: str
    submission_id: int
    submitted_at: str


class StudentSubmissionDetail(BaseModel):
    """Full detail of a single student submission."""

    id: int
    student_name: str
    problem_description: Optional[str]
    code: str
    additional_files: List[AdditionalFile]
    test_results: Optional[List[Dict[str, Any]]]
    score: Optional[float]
    submitted_at: str


class StudentSubmissionsListResponse(BaseModel):
    """Paginated list of student submissions."""

    total: int
    page: int
    page_size: int
    submissions: List[StudentSubmissionDetail]


@student_submission_router.post(
    "/student_submission", response_model=StudentSubmissionResponse
)
async def student_submission(
    request_data: StudentSubmissionRequest,
) -> StudentSubmissionResponse:
    """
    Store a student code submission for teacher review.

    Submissions are persisted in the database and can be retrieved
    later via the listing and detail endpoints below.

    :param request_data: Student name, problem description, code, and optional extra files
    :return: Confirmation including the stored submission ID
    """
    db = ExamSessionsTable()
    try:
        submission_id = db.store_exercise_submission(
            student_name=request_data.student_name,
            problem_description=request_data.problem_description,
            code=request_data.code,
            additional_files=(
                [f.model_dump() for f in request_data.additional_files]
                if request_data.additional_files
                else None
            ),
        )
    finally:
        db.close()

    if submission_id is None:
        raise HTTPException(status_code=500, detail="Failed to store submission")

    from datetime import datetime

    return StudentSubmissionResponse(
        success=True,
        message="Your code has been successfully submitted to your teacher for review!",
        submission_id=submission_id,
        submitted_at=datetime.now().isoformat(),
    )


@student_submission_router.get(
    "/student_submissions", response_model=StudentSubmissionsListResponse
)
async def list_student_submissions(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> StudentSubmissionsListResponse:
    """
    List all student submissions with pagination.

    :param page: Page number (starts at 1)
    :param page_size: Number of items per page (max 100)
    :return: Paginated list of submissions
    """
    db = ExamSessionsTable()
    try:
        total, rows = db.get_exercise_submissions(page=page, page_size=page_size)
    finally:
        db.close()

    submissions = [
        StudentSubmissionDetail(
            id=row["id"],
            student_name=row["student_name"],
            problem_description=row["problem_description"],
            code=row["code"],
            additional_files=[
                AdditionalFile(**f) for f in (row.get("additional_files") or [])
            ],
            test_results=row.get("test_results"),
            score=row.get("score"),
            submitted_at=row["submitted_at"],
        )
        for row in rows
    ]

    return StudentSubmissionsListResponse(
        total=total,
        page=page,
        page_size=page_size,
        submissions=submissions,
    )


@student_submission_router.get(
    "/student_submissions/{submission_id}",
    response_model=StudentSubmissionDetail,
)
async def get_student_submission_detail(
    submission_id: int,
) -> StudentSubmissionDetail:
    """
    Retrieve a specific student submission by ID.

    :param submission_id: The submission ID returned when the submission was stored
    :return: Full submission details including code and any test results
    """
    db = ExamSessionsTable()
    try:
        row = db.get_exercise_submission_by_id(submission_id)
    finally:
        db.close()

    if not row:
        raise HTTPException(status_code=404, detail="Submission not found")

    return StudentSubmissionDetail(
        id=row["id"],
        student_name=row["student_name"],
        problem_description=row["problem_description"],
        code=row["code"],
        additional_files=[
            AdditionalFile(**f) for f in (row.get("additional_files") or [])
        ],
        test_results=row.get("test_results"),
        score=row.get("score"),
        submitted_at=row["submitted_at"],
    )
