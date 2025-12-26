"""FastAPI routes for exam session management."""
import sys
import uuid
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

sys.path.append(".")

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from src.apps.server.database.exam_sessions import ExamSessionsTable
from src.core.config_parser.parsers import ConfigParser
from src.core.execution.data import ExecutionManagerFactory
from src.core.execution.manager import ExecutionManager

exam_session_router = APIRouter()


class CreateSessionRequest(BaseModel):
    """Request model for creating an exam session."""
    config_data: Dict[str, Any]


class CreateSessionResponse(BaseModel):
    """Response model for creating an exam session."""
    session_id: str
    session_url: str


class TestCodeRequest(BaseModel):
    """Request model for testing student code."""
    session_id: str
    student_id: str
    code: str


class TestCodeResponse(BaseModel):
    """Response model for testing student code."""
    test_results: List[Dict[str, Any]]
    total_tests: int
    passed_tests: int
    score: float


class SubmitCodeRequest(BaseModel):
    """Request model for submitting student code."""
    session_id: str
    student_id: str
    code: str


class SubmitCodeResponse(BaseModel):
    """Response model for code submission."""
    success: bool
    message: str
    test_results: Optional[List[Dict[str, Any]]] = None
    score: Optional[float] = None


class SessionSubmissionsResponse(BaseModel):
    """Response model for session submissions."""
    session_id: str
    total_submissions: int
    submissions: List[Dict[str, Any]]


@exam_session_router.post("/api/exam/create_session", response_model=CreateSessionResponse)
async def create_exam_session(request: CreateSessionRequest) -> CreateSessionResponse:
    """
    Create a new exam session with the given configuration.
    
    :param request: Configuration data for the exam
    :return: Session ID and URL for students
    """
    # Generate a unique session ID
    session_id = str(uuid.uuid4())[:8]
    
    # Store the session in the database
    exam_db = ExamSessionsTable()
    try:
        success = exam_db.create_session(session_id, request.config_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create session")
        
        # Generate the student URL
        session_url = f"/student/{session_id}"
        
        return CreateSessionResponse(
            session_id=session_id,
            session_url=session_url
        )
    finally:
        exam_db.close()


@exam_session_router.get("/api/exam/session/{session_id}")
async def get_exam_session(session_id: str) -> Dict[str, Any]:
    """
    Get exam session details.
    
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


@exam_session_router.post("/api/exam/test_code", response_model=TestCodeResponse)
async def test_student_code(request: TestCodeRequest) -> TestCodeResponse:
    """
    Test student code without submitting it (for practice).
    
    :param request: Student code and session information
    :return: Test results
    """
    # Get the session configuration
    exam_db = ExamSessionsTable()
    try:
        session = exam_db.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if not session["is_active"]:
            raise HTTPException(status_code=403, detail="Session is no longer active")
    finally:
        exam_db.close()
    
    # Parse the configuration
    parser = ConfigParser()
    test_suite_config = parser.parse_from_json(session["config_data"])
    
    # Create a temporary file for the student's code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        temp_file.write(request.code)
        temp_file_path = temp_file.name
    
    try:
        # Create execution manager data
        execution_manager_data = ExecutionManagerFactory._create_execution_manager_data(
            test_suite_config, temp_file_path
        )
        
        # Run the tests
        manager = ExecutionManager()
        test_results = []
        for data in execution_manager_data:
            result = manager.run(data)
            test_results.append(result.to_dict())
        
        # Calculate statistics
        total_tests = len(test_results)
        passed_tests = len([r for r in test_results if r['result'] == 'ComparisonResult.MATCH'])
        score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return TestCodeResponse(
            test_results=test_results,
            total_tests=total_tests,
            passed_tests=passed_tests,
            score=round(score, 2)
        )
    finally:
        # Clean up temporary file
        Path(temp_file_path).unlink(missing_ok=True)


@exam_session_router.post("/api/exam/submit_code", response_model=SubmitCodeResponse)
async def submit_student_code(request: SubmitCodeRequest) -> SubmitCodeResponse:
    """
    Submit student code for final grading.
    
    :param request: Student code and session information
    :return: Submission confirmation with test results
    """
    # Get the session configuration
    exam_db = ExamSessionsTable()
    try:
        session = exam_db.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if not session["is_active"]:
            raise HTTPException(status_code=403, detail="Session is no longer active")
        
        # Check if student already submitted
        existing_submission = exam_db.get_student_submission(
            request.session_id, 
            request.student_id
        )
        if existing_submission:
            raise HTTPException(
                status_code=400, 
                detail="You have already submitted your work for this exam"
            )
    
        # Parse the configuration
        parser = ConfigParser()
        test_suite_config = parser.parse_from_json(session["config_data"])
        
        # Create a temporary file for the student's code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(request.code)
            temp_file_path = temp_file.name
        
        try:
            # Create execution manager data
            execution_manager_data = ExecutionManagerFactory._create_execution_manager_data(
                test_suite_config, temp_file_path
            )
            
            # Run the tests
            manager = ExecutionManager()
            test_results = []
            for data in execution_manager_data:
                result = manager.run(data)
                test_results.append(result.to_dict())
            
            # Calculate statistics
            total_tests = len(test_results)
            passed_tests = len([r for r in test_results if r['result'] == 'ComparisonResult.MATCH'])
            score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            # Store the submission
            exam_db.submit_student_work(
                request.session_id,
                request.student_id,
                request.code,
                test_results,
                score
            )
            
            return SubmitCodeResponse(
                success=True,
                message="Code submitted successfully",
                test_results=test_results,
                score=round(score, 2)
            )
        finally:
            # Clean up temporary file
            Path(temp_file_path).unlink(missing_ok=True)
    finally:
        exam_db.close()


@exam_session_router.get("/api/exam/submissions/{session_id}", response_model=SessionSubmissionsResponse)
async def get_session_submissions(session_id: str) -> SessionSubmissionsResponse:
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
            submissions=submissions
        )
    finally:
        exam_db.close()


@exam_session_router.post("/api/exam/end_session/{session_id}")
async def end_exam_session(session_id: str) -> Dict[str, str]:
    """
    End an exam session (no more submissions allowed).
    
    :param session_id: The session ID to end
    :return: Success message
    """
    exam_db = ExamSessionsTable()
    try:
        success = exam_db.end_session(session_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to end session")
        
        return {"message": "Session ended successfully"}
    finally:
        exam_db.close()
