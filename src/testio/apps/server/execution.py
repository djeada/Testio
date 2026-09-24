"""Shared server-side execution of a submission against a test suite.

Every route that runs submitted code goes through :func:`run_submission` (or
:func:`run_prepared_tests` for already-built test data), which

1. creates a fresh private temporary directory for the request,
2. writes the submission there under a name/suffix suited to the config,
3. compiles it when the config has a ``compile_command`` (artifacts stay in
   the same directory),
4. runs every test through the shared execution queue with that directory as
   the program's working directory (so relative paths cannot reach the
   server's files, e.g. its SQLite databases), and
5. removes the directory - including compiled artifacts - afterwards.
"""

import asyncio
import logging
import re
import shutil
import tempfile
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from testio.core.config_parser.data import TestSuiteConfig
from testio.core.execution.command_utils import infer_source_suffix
from testio.core.execution.data import (
    ComparisonOutputData,
    ComparisonResult,
    ExecutionManagerFactory,
    ExecutionManagerInputData,
    as_lines,
)
from testio.core.execution.manager import ExecutionManager
from testio.core.execution.queue import ExecutionPriority, get_execution_queue
from testio.core.execution.task_runner import run_single_test

logger = logging.getLogger(__name__)

# Extra seconds a queued test may take beyond its own timeout (process start,
# teardown) before the waiter gives up on it.
_EXECUTION_GRACE_SECONDS = 30
# Upper bound for the compile step (the compiler itself times out at 30s).
_BUILD_TIMEOUT_SECONDS = 90

_SAFE_STEM = re.compile(r"[^A-Za-z0-9_\-]")
_SAFE_SUFFIX = re.compile(r"^\.[A-Za-z0-9]{1,10}$")


@dataclass
class SubmissionRun:
    """Outcome of running one submission against a test suite."""

    results: List[ComparisonOutputData] = field(default_factory=list)
    compile_error: str = ""

    @property
    def test_results(self) -> List[Dict[str, Any]]:
        return [result.to_dict() for result in self.results]

    @property
    def total_tests(self) -> int:
        return len(self.results)

    @property
    def passed_tests(self) -> int:
        return sum(1 for r in self.results if r.result == ComparisonResult.MATCH)

    @property
    def score(self) -> float:
        total = self.total_tests
        return round(self.passed_tests / total * 100, 2) if total else 0.0


def _sanitize_stem(stem: str) -> str:
    cleaned = _SAFE_STEM.sub("_", stem)[:64].lstrip("-_")
    return cleaned or "submission"


def source_filename(test_suite_config: TestSuiteConfig, filename: str = "") -> str:
    """Pick a safe file name for a submission.

    The config's own file name is preferred when its suffix matches (Java, for
    instance, requires the file to be named after its public class).
    """
    upload_suffix = Path(filename).suffix if filename else ""
    if upload_suffix and not _SAFE_SUFFIX.match(upload_suffix):
        filename = ""
    suffix = infer_source_suffix(
        filename=filename,
        command=test_suite_config.run_command or test_suite_config.command,
        compile_command=test_suite_config.compile_command,
        path=test_suite_config.path,
    )
    if not _SAFE_SUFFIX.match(suffix):
        suffix = ".txt"

    config_path = Path(test_suite_config.path or "")
    if config_path.suffix == suffix and config_path.stem:
        stem = config_path.stem
    elif filename:
        stem = Path(filename).stem
    else:
        stem = "submission"
    return f"{_sanitize_stem(stem)}{suffix}"


def _build_in_directory(
    test_suite_config: TestSuiteConfig,
    source: Union[str, bytes],
    filename: str,
    work_dir: str,
) -> List[ExecutionManagerInputData]:
    """Write the submission into ``work_dir``, compile it if needed, and
    return per-test data that runs inside ``work_dir``."""
    source_path = Path(work_dir) / source_filename(test_suite_config, filename)
    payload = source.encode("utf-8") if isinstance(source, str) else source
    source_path.write_bytes(payload)

    data_list = ExecutionManagerFactory.build_for_file(
        test_suite_config, str(source_path), output_dir=str(Path(work_dir) / "build")
    )
    for data in data_list:
        data.cwd = work_dir
    return data_list


def _timeout_result(data: ExecutionManagerInputData) -> ComparisonOutputData:
    return ComparisonOutputData(
        input="\n".join(as_lines(data.input)),
        expected_output="\n".join(as_lines(data.output)),
        error="Execution did not finish in time.",
        result=ComparisonResult.TIMEOUT,
    )


async def _run_tests(
    data_list: List[ExecutionManagerInputData], priority: ExecutionPriority
) -> List[ComparisonOutputData]:
    queue = get_execution_queue()
    # Bound this request's footprint in the shared queue: a suite with many
    # tests must not fill the queue on its own.
    window = asyncio.Semaphore(queue.max_workers)

    async def run_one(data: ExecutionManagerInputData) -> ComparisonOutputData:
        if data.compile_error:
            # Nothing to execute; the manager just reports the compile error.
            return ExecutionManager().run(data)
        async with window:
            try:
                return await queue.submit_async(
                    run_single_test,
                    data,
                    priority=priority,
                    timeout=(data.timeout or 0) + _EXECUTION_GRACE_SECONDS,
                )
            except TimeoutError:
                return _timeout_result(data)

    outcomes = await asyncio.gather(
        *(run_one(data) for data in data_list), return_exceptions=True
    )
    # Every task has finished (or failed) at this point, so the caller may
    # safely remove the working directory before an error propagates.
    for outcome in outcomes:
        if isinstance(outcome, BaseException):
            raise outcome
    return list(outcomes)  # type: ignore[arg-type]


def _remove_directory(path: str) -> None:
    shutil.rmtree(path, ignore_errors=True)


async def run_submission(
    test_suite_config: TestSuiteConfig,
    source: Union[str, bytes],
    *,
    filename: str = "",
    priority: ExecutionPriority = ExecutionPriority.NORMAL,
) -> SubmissionRun:
    """Compile (if configured) and test ``source`` in an isolated directory.

    :raises QueueFullError: when the execution queue is saturated.
    """
    queue = get_execution_queue()
    work_dir = tempfile.mkdtemp(prefix="testio-run-")
    try:
        data_list = await queue.submit_async(
            _build_in_directory,
            test_suite_config,
            source,
            filename,
            work_dir,
            priority=priority,
            timeout=_BUILD_TIMEOUT_SECONDS,
        )
        compile_error = next(
            (d.compile_error for d in data_list if d.compile_error), ""
        )
        results = await _run_tests(data_list, priority)
    finally:
        await asyncio.to_thread(_remove_directory, work_dir)
    return SubmissionRun(results=results, compile_error=compile_error)


async def run_prepared_tests(
    data_list: List[ExecutionManagerInputData],
    *,
    priority: ExecutionPriority = ExecutionPriority.NORMAL,
    work_dir: Optional[str] = None,
) -> List[ComparisonOutputData]:
    """Run already-built test data with ``work_dir`` (or a fresh temporary
    directory, removed afterwards) as the working directory."""
    own_dir = work_dir is None
    directory = work_dir or tempfile.mkdtemp(prefix="testio-run-")
    try:
        prepared = [replace(data, cwd=directory) for data in data_list]
        return await _run_tests(prepared, priority)
    finally:
        if own_dir:
            await asyncio.to_thread(_remove_directory, directory)
