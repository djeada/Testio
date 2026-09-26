"""Tests for ExecutionManager."""

import sys
from pathlib import Path

from testio.core.execution.data import ComparisonResult, ExecutionManagerInputData
from testio.core.execution.manager import ExecutionManager


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


def test_compile_error_is_reported_not_dropped(tmp_path):
    """A submission that fails to compile must show up as a failed result."""
    import shutil

    import pytest

    from testio.core.config_parser.data import TestData, TestSuiteConfig
    from testio.core.execution.data import ComparisonResult, ExecutionManagerFactory
    from testio.core.execution.manager import ExecutionManager

    if shutil.which("gcc") is None:
        pytest.skip("gcc not available")

    (tmp_path / "bad.c").write_text("int main( {")
    (tmp_path / "good.c").write_text('#include <stdio.h>\nint main(){puts("ok");}')
    config = TestSuiteConfig(
        command="",
        path=str(tmp_path),
        tests=[TestData(input=[], output=["ok"], timeout=5)],
        compile_command="gcc {source} -o {output}",
    )

    data = ExecutionManagerFactory.from_test_suite_config_server(config)
    results = {
        Path(path).name: ExecutionManager().run(items[0])
        for path, items in data.items()
    }

    assert results["good.c"].result == ComparisonResult.MATCH
    assert results["bad.c"].result == ComparisonResult.EXECUTION_ERROR
    assert "Compilation failed" in results["bad.c"].error
