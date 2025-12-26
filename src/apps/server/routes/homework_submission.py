"""This module defines a FastAPI router for handling homework submissions with multiple student programs."""
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List

sys.path.append(".")

from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel

from src.core.config_parser.parsers import ConfigParser
from src.core.execution.data import ExecutionManagerFactory, ComparisonResult
from src.core.execution.manager import ExecutionManager

homework_submission_router: APIRouter = APIRouter()


class HomeworkSubmissionResponse(BaseModel):
    """Response model for homework submission endpoint."""
    student_results: List[Dict[str, Any]]
    total_students: int


@homework_submission_router.post("/homework_submission", response_model=HomeworkSubmissionResponse)
async def homework_submission(
    config_file: UploadFile = File(..., description="Configuration JSON file"),
    student_files: List[UploadFile] = File(..., description="List of student program files")
) -> HomeworkSubmissionResponse:
    """
    Test multiple student programs against a configuration file.
    
    :param config_file: The configuration JSON file containing test specifications
    :param student_files: List of student program files to test
    :return: Test results for each student program
    """
    # Read and parse the configuration file
    config_content = await config_file.read()
    import json
    config_json = json.loads(config_content.decode('utf-8'))
    
    parser = ConfigParser()
    test_suite_config = parser.parse_from_json(config_json)
    
    # Initialize execution manager
    manager = ExecutionManager()
    
    # Store results for all students
    student_results = []
    
    # Process each student file
    for student_file in student_files:
        student_content = await student_file.read()
        
        # Create a temporary file for the student's program
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(student_content.decode('utf-8'))
            temp_file_path = temp_file.name
        
        try:
            # Create execution manager data for this student's program
            execution_manager_data = ExecutionManagerFactory._create_execution_manager_data(
                test_suite_config, temp_file_path
            )
            
            # Run all tests for this student
            test_results = []
            for data in execution_manager_data:
                result = manager.run(data)
                test_results.append(result.to_dict())
            
            # Calculate statistics
            total_tests = len(test_results)
            passed_tests = len([r for r in test_results if 'MATCH' in r['result']])
            score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            student_results.append({
                "student_name": student_file.filename,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "score": round(score, 2),
                "test_results": test_results
            })
        finally:
            # Clean up temporary file
            Path(temp_file_path).unlink(missing_ok=True)
    
    return HomeworkSubmissionResponse(
        student_results=student_results,
        total_students=len(student_files)
    )
