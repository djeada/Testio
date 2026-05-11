"""Tests for the standard Runner."""

from src.core.execution.data import ExecutionInputData
from src.core.execution.runner import Runner


def test_runner_preserves_stdout_without_trailing_newline():
    runner = Runner()
    result = runner.run(
        ExecutionInputData(
            command="python3 -c \"import sys; sys.stdout.write('OK')\"",
            input="",
            timeout=5,
        )
    )

    assert result.timeout is False
    assert result.stderr == ""
    assert result.stdout == "OK"


def test_runner_returns_timeout_flag():
    runner = Runner()
    result = runner.run(
        ExecutionInputData(
            command='python3 -c "import time; time.sleep(2)"',
            input="",
            timeout=1,
        )
    )

    assert result.timeout is True
