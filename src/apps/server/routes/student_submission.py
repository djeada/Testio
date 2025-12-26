"""This module defines a FastAPI router for handling student code submissions to teachers."""
import sys
from datetime import datetime
import uuid

sys.path.append(".")

from fastapi import APIRouter
from pydantic import BaseModel

student_submission_router: APIRouter = APIRouter()


class StudentSubmissionRequest(BaseModel):
    """Request model for student submission endpoint."""
    student_name: str
    problem_description: str
    code: str


class StudentSubmissionResponse(BaseModel):
    """Response model for student submission endpoint."""
    success: bool
    message: str
    submission_id: str
    submitted_at: str


@student_submission_router.post("/student_submission", response_model=StudentSubmissionResponse)
async def student_submission(request_data: StudentSubmissionRequest) -> StudentSubmissionResponse:
    """
    Handle student code submission to teacher.
    
    :param request_data: Student submission data including name, problem description, and code
    :return: Confirmation of submission
    """
    # Generate a unique submission ID using UUID
    submission_id = f"SUB-{uuid.uuid4().hex[:12].upper()}"
    submitted_at = datetime.now().isoformat()
    
    # In a real implementation, this would:
    # 1. Store the submission in a database
    # 2. Notify the teacher
    # 3. Generate a unique submission ID
    
    # For now, we'll just return a success response
    return StudentSubmissionResponse(
        success=True,
        message="Your code has been successfully submitted to your teacher for review!",
        submission_id=submission_id,
        submitted_at=submitted_at
    )
