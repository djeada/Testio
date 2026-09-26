"""This module defines a FastAPI router for executing tests and returning the results in JSON format.

This is the student practice endpoint: it runs the submitted script against
the test suite the teacher loaded (``/update_test_suite`` or the config file
given to ``testio-server``). The client cannot supply its own config or
command.
"""

import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from testio.apps.server.database.configuration_data import (
    load_suite_config_json,
    parse_config_data,
)
from testio.apps.server.execution import run_prepared_tests, run_submission
from testio.apps.server.validation import MAX_CODE_CHARS
from testio.core.config_parser.parsers import ConfigNotParsable, ConfigParser
from testio.core.execution.command_utils import (
    infer_source_suffix,
    replace_command_path,
)
from testio.core.execution.data import (
    ComparisonOutputData,
    ComparisonResult,
    ExecutionManagerInputData,
)
from testio.core.execution.manager import ExecutionManager
from testio.core.execution.queue import ExecutionPriority

execute_tests_router: APIRouter = APIRouter()


class ExecuteTestsRequest(BaseModel):
    """Request model for execute_tests endpoint."""

    script_text: str = Field(..., max_length=MAX_CODE_CHARS)


def _summarise(
    name: str, results: List[ComparisonOutputData]
) -> Tuple[Dict[str, Any], int, int]:
    num_tests = len(results)
    passed_tests = sum(1 for r in results if r.result == ComparisonResult.MATCH)
    ratio = (passed_tests / num_tests * 100) if num_tests > 0 else 0.0
    entry = {
        "tests": [result.to_dict() for result in results],
        "passed_tests_ratio": ratio,
        "name": name,
    }
    return entry, num_tests, passed_tests


def _rewrite_for_temp_file(
    path: str,
    script_text: str,
    exec_data: List[ExecutionManagerInputData],
    temp_dir: str,
) -> List[ExecutionManagerInputData]:
    """Write ``script_text`` into ``temp_dir`` and point legacy test data at it."""
    suffix = infer_source_suffix(
        path=path,
        command=exec_data[0].command if exec_data else "",
    )
    temp_path = Path(temp_dir) / f"{Path(path).stem}{suffix}"
    temp_path.write_text(script_text, encoding="utf-8")
    return [
        replace(
            data,
            command=replace_command_path(data.command, path, str(temp_path)),
            cwd=temp_dir,
        )
        for data in exec_data
    ]


def process_file_for_server(
    args: Tuple[str, str, List[ExecutionManagerInputData]],
) -> Tuple[str, List[ComparisonOutputData], int, int, float]:
    """
    Run legacy stored test data against ``script_text`` synchronously.

    The script is written to a private temporary directory, which is also the
    program's working directory, and removed afterwards.

    :param args: A tuple containing (path, script_text, exec_data)
    :return: A tuple containing (path, results, total_tests, passed_tests, ratio)
    """
    path, script_text, exec_data = args
    with tempfile.TemporaryDirectory(prefix="testio-run-") as temp_dir:
        manager = ExecutionManager()
        results = [
            manager.run(data)
            for data in _rewrite_for_temp_file(path, script_text, exec_data, temp_dir)
        ]

    entry, num_tests, passed_tests = _summarise(Path(path).name, results)
    return path, results, num_tests, passed_tests, entry["passed_tests_ratio"]


async def _run_legacy(
    execution_manager_data: Dict[str, List[ExecutionManagerInputData]],
    script_text: str,
) -> List[Tuple[Dict[str, Any], int, int]]:
    summaries = []
    for path, exec_data in execution_manager_data.items():
        with tempfile.TemporaryDirectory(prefix="testio-run-") as temp_dir:
            prepared = _rewrite_for_temp_file(path, script_text, exec_data, temp_dir)
            results = await run_prepared_tests(
                prepared, priority=ExecutionPriority.HIGH, work_dir=temp_dir
            )
        summaries.append(_summarise(Path(path).name, results))
    return summaries


@execute_tests_router.post("/execute_tests")
async def execute_tests(request_data: ExecuteTestsRequest) -> Dict[str, Any]:
    """Executes tests using the provided script text and returns the results in JSON format.

    :return: The JSON-encoded test results.
    :raises HTTPException 404: when the teacher has not loaded a test suite.
    """
    script_text: str = request_data.script_text
    suite_json = load_suite_config_json()

    if suite_json is not None:
        try:
            test_suite_config = ConfigParser().parse_from_json(suite_json)
        except ConfigNotParsable:
            raise HTTPException(
                status_code=409, detail="The loaded test suite is no longer valid"
            )
        run = await run_submission(
            test_suite_config, script_text, priority=ExecutionPriority.HIGH
        )
        name = Path(test_suite_config.path).name or "submission"
        summaries = [_summarise(name, run.results)]
    else:
        execution_manager_data = parse_config_data()
        if not execution_manager_data:
            raise HTTPException(
                status_code=404,
                detail="No test suite is loaded. Ask your teacher to load one.",
            )
        summaries = await _run_legacy(execution_manager_data, script_text)

    json_response: Dict[str, Any] = {
        "total_tests": 0,
        "total_passed_tests": 0,
        "results": [],
    }
    for entry, num_tests, passed_tests in summaries:
        json_response["total_tests"] += num_tests
        json_response["total_passed_tests"] += passed_tests
        json_response["results"].append(entry)
    return json_response
