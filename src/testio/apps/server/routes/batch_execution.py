"""This module defines FastAPI routes for batch test execution."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from testio.apps.server.auth import require_teacher_auth
from testio.apps.server.execution import run_submission
from testio.apps.server.uploads import parse_config_or_400
from testio.apps.server.validation import MAX_CODE_CHARS
from testio.core.execution.command_utils import infer_source_suffix
from testio.core.execution.queue import ExecutionPriority
from testio.core.execution.result_utils import result_passed

batch_router: APIRouter = APIRouter(tags=["Batch Execution"])


class TestCase(BaseModel):
    """A single test case configuration."""

    input: List[str] = Field(
        default_factory=list, description="Input data for the test"
    )
    output: List[str] = Field(default_factory=list, description="Expected output data")
    timeout: int = Field(default=10, description="Timeout in seconds", ge=1, le=300)
    use_regex: bool = Field(default=False, description="Whether to use regex matching")
    interleaved: bool = Field(
        default=False, description="Whether to use interleaved I/O"
    )


class BatchTestConfig(BaseModel):
    """Configuration for a single program test."""

    name: str = Field(
        ..., max_length=200, description="Name identifier for this test configuration"
    )
    command: str = Field(
        ..., max_length=500, description="Command to execute (e.g., 'python3')"
    )
    code: str = Field(..., max_length=MAX_CODE_CHARS, description="The code to test")
    tests: List[TestCase] = Field(..., max_length=200, description="List of test cases")


class BatchTestRequest(BaseModel):
    """Request model for batch test execution."""

    configurations: List[BatchTestConfig] = Field(
        ..., description="List of test configurations to execute"
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


async def run_single_config(config: BatchTestConfig) -> ConfigResult:
    """
    Run tests for a single configuration through the shared execution helper.

    :param config: The test configuration
    :return: ConfigResult with test results
    """
    test_suite_config = parse_config_or_400(
        {
            "command": config.command,
            "path": f"submission{infer_source_suffix(command=config.command)}",
            "tests": [
                {
                    "input": t.input,
                    "output": t.output,
                    "timeout": t.timeout,
                    "use_regex": t.use_regex,
                    "interleaved": t.interleaved,
                }
                for t in config.tests
            ],
        }
    )

    run = await run_submission(
        test_suite_config, config.code, priority=ExecutionPriority.LOW
    )
    test_results = [
        TestResult(
            input=result.input,
            expected_output=result.expected_output,
            actual_output=result.output,
            error=result.error,
            passed=result_passed(result.to_dict()),
        )
        for result in run.results
    ]

    return ConfigResult(
        name=config.name,
        total_tests=run.total_tests,
        passed_tests=run.passed_tests,
        failed_tests=run.total_tests - run.passed_tests,
        score=run.score,
        test_results=test_results,
    )


@batch_router.post("/api/batch/execute", response_model=BatchTestResponse)
async def batch_execute_tests(
    request: BatchTestRequest,
    _auth: None = Depends(require_teacher_auth),
) -> BatchTestResponse:
    """
    Execute tests for multiple configurations in batch.

    This endpoint allows you to test multiple code samples against
    different test configurations in a single request.

    :param request: BatchTestRequest with configurations to test
    :return: BatchTestResponse with aggregated results
    """
    if not request.configurations:
        raise HTTPException(
            status_code=400, detail="At least one configuration is required"
        )

    if len(request.configurations) > 50:
        raise HTTPException(
            status_code=400,
            detail="Maximum 50 configurations allowed per batch request",
        )

    # Each configuration's tests run through the shared execution queue.
    results = [await run_single_config(config) for config in request.configurations]

    # Calculate overall statistics
    total_tests = sum(r.total_tests for r in results)
    total_passed = sum(r.passed_tests for r in results)
    overall_score = (total_passed / total_tests * 100) if total_tests > 0 else 0.0

    return BatchTestResponse(
        total_configurations=len(results),
        total_tests=total_tests,
        total_passed=total_passed,
        overall_score=round(overall_score, 2),
        results=results,
    )
