"""Tests for ExecutionManager."""

import sys

from src.core.execution.data import ComparisonResult, ExecutionManagerInputData
from src.core.execution.manager import ExecutionManager


def _make_input(command, inputs, outputs, interleaved=False, timeout=10):
    return ExecutionManagerInputData(
        command=command,
        input=inputs,
        output=outputs,
        timeout=timeout,
        interleaved=interleaved,
        use_regex=False,
        unordered=False,
    )


def test_run_simple_match():
    """Echo command should produce MATCH."""
    data = _make_input(
        command=f"{sys.executable} -c \"print('hello')\"",
        inputs=[],
        outputs=["hello"],
    )
    result = ExecutionManager().run(data)
    assert result.result == ComparisonResult.MATCH


def test_run_timeout():
    """Long-running process should return TIMEOUT result."""
    data = _make_input(
        command=f'{sys.executable} -c "import time; time.sleep(60)"',
        inputs=[],
        outputs=["anything"],
        timeout=1,
    )
    result = ExecutionManager().run(data)
    assert result.result == ComparisonResult.TIMEOUT


def test_run_mismatch():
    """Wrong output should return MISMATCH."""
    data = _make_input(
        command=f"{sys.executable} -c \"print('wrong')\"",
        inputs=[],
        outputs=["expected"],
    )
    result = ExecutionManager().run(data)
    assert result.result == ComparisonResult.MISMATCH
