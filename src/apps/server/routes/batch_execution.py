"""This module defines FastAPI routes for batch test execution."""
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List
from concurrent.futures import ProcessPoolExecutor

sys.path.append(".")

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.core.config_parser.parsers import ConfigParser
from src.core.execution.data import (
    ExecutionManagerFactory, 
    ComparisonResult, 
    ComparisonOutputData
)
from src.core.execution.manager import ExecutionManager

batch_router: APIRouter = APIRouter(tags=["Batch Execution"])


class TestCase(BaseModel):
    """A single test case configuration."""
    input: List[str] = Field(default_factory=list, description="Input data for the test")
    output: List[str] = Field(default_factory=list, description="Expected output data")
    timeout: int = Field(default=10, description="Timeout in seconds", ge=1, le=300)
    use_regex: bool = Field(default=False, description="Whether to use regex matching")
    interleaved: bool = Field(default=False, description="Whether to use interleaved I/O")


class BatchTestConfig(BaseModel):
    """Configuration for a single program test."""
    name: str = Field(..., description="Name identifier for this test configuration")
    command: str = Field(..., description="Command to execute (e.g., 'python3')")
    code: str = Field(..., description="The code to test")
    tests: List[TestCase] = Field(..., description="List of test cases")


class BatchTestRequest(BaseModel):
    """Request model for batch test execution."""
    configurations: List[BatchTestConfig] = Field(
        ..., 
        description="List of test configurations to execute"
    )


class TestResult(BaseModel):
    """Result of a single test case."""
    input: str
    expected_output: str
    actual_output: str
    error: str
    passed: bool


class ConfigResult(BaseModel):
    """Result for a single configuration."""
    name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    score: float
    test_results: List[TestResult]


class BatchTestResponse(BaseModel):
    """Response model for batch test execution."""
    total_configurations: int
    total_tests: int
    total_passed: int
    overall_score: float
    results: List[ConfigResult]


def run_single_config(config: BatchTestConfig) -> ConfigResult:
    """
    Run tests for a single configuration.
    
    :param config: The test configuration
    :return: ConfigResult with test results
    """
    # Create a temporary file for the code
    with tempfile.NamedTemporaryFile(
        mode='w', 
        suffix='.py', 
        delete=False
    ) as temp_file:
        temp_file.write(config.code)
        temp_file_path = temp_file.name
    
    try:
        # Create test suite config
        config_data = {
            "command": config.command,
            "path": temp_file_path,
            "tests": [
                {
                    "input": t.input,
                    "output": t.output,
                    "timeout": t.timeout,
                    "use_regex": t.use_regex,
                    "interleaved": t.interleaved
                }
                for t in config.tests
            ]
        }
        
        parser = ConfigParser()
        test_suite_config = parser.parse_from_json(config_data)
        
        # Create execution manager data
        execution_manager_data = ExecutionManagerFactory._create_execution_manager_data(
            test_suite_config, temp_file_path
        )
        
        # Run tests
        manager = ExecutionManager()
        test_results = []
        
        for data in execution_manager_data:
            result = manager.run(data)
            passed = result.result == ComparisonResult.MATCH
            test_results.append(TestResult(
                input=result.input,
                expected_output=result.expected_output,
                actual_output=result.output,
                error=result.error,
                passed=passed
            ))
        
        # Calculate statistics
        total_tests = len(test_results)
        passed_tests = sum(1 for r in test_results if r.passed)
        score = (passed_tests / total_tests * 100) if total_tests > 0 else 0.0
        
        return ConfigResult(
            name=config.name,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=total_tests - passed_tests,
            score=round(score, 2),
            test_results=test_results
        )
    finally:
        # Clean up temporary file
        Path(temp_file_path).unlink(missing_ok=True)


@batch_router.post("/api/batch/execute", response_model=BatchTestResponse)
async def batch_execute_tests(request: BatchTestRequest) -> BatchTestResponse:
    """
    Execute tests for multiple configurations in batch.
    
    This endpoint allows you to test multiple code samples against
    different test configurations in a single request.
    
    :param request: BatchTestRequest with configurations to test
    :return: BatchTestResponse with aggregated results
    """
    if not request.configurations:
        raise HTTPException(
            status_code=400, 
            detail="At least one configuration is required"
        )
    
    if len(request.configurations) > 50:
        raise HTTPException(
            status_code=400,
            detail="Maximum 50 configurations allowed per batch request"
        )
    
    results = []
    
    # Process each configuration
    for config in request.configurations:
        result = run_single_config(config)
        results.append(result)
    
    # Calculate overall statistics
    total_tests = sum(r.total_tests for r in results)
    total_passed = sum(r.passed_tests for r in results)
    overall_score = (total_passed / total_tests * 100) if total_tests > 0 else 0.0
    
    return BatchTestResponse(
        total_configurations=len(results),
        total_tests=total_tests,
        total_passed=total_passed,
        overall_score=round(overall_score, 2),
        results=results
    )
