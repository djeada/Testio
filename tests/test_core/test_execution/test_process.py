"""Tests for the hardened subprocess layer."""

import os
import sys
import time

import pytest

from testio.core.execution.process import build_child_env, run_process

PY = sys.executable
posix_only = pytest.mark.skipif(os.name != "posix", reason="POSIX process groups")


def test_captures_stdout_stderr_and_exit_code():
    result = run_process(
        [
            PY,
            "-c",
            "import sys; print('out'); print('err', file=sys.stderr); sys.exit(3)",
        ]
    )
    assert result.stdout == "out\n"
    assert result.stderr == "err\n"
    assert result.returncode == 3
    assert not result.timed_out


def test_feeds_stdin():
    result = run_process([PY, "-c", "print(input()[::-1])"], input_text="abc\n")
    assert result.stdout == "cba\n"


def test_invalid_utf8_output_does_not_crash():
    result = run_process([PY, "-c", "import sys; sys.stdout.buffer.write(b'\\xff ok')"])
    assert result.stdout == "� ok"


def test_timeout_is_reported():
    start = time.monotonic()
    result = run_process([PY, "-c", "import time; time.sleep(30)"], timeout=0.5)
    assert result.timed_out
    assert time.monotonic() - start < 10


def test_output_is_capped_and_program_killed():
    result = run_process(
        [PY, "-c", "while True: print('x' * 1000)"],
        timeout=20,
        max_output_bytes=10_000,
    )
    assert result.output_truncated
    assert len(result.stdout) == 10_000
    assert not result.timed_out


@posix_only
def test_background_children_do_not_block_or_survive(tmp_path):
    marker = tmp_path / "survived"
    script = (
        "import subprocess, sys; "
        f"subprocess.Popen([sys.executable, '-c', "
        f'\'import time; time.sleep(3); open(r"{marker}", "w").close()\']); '
        "print('parent done')"
    )
    start = time.monotonic()
    result = run_process([PY, "-c", script], timeout=10)
    assert result.stdout == "parent done\n"
    assert time.monotonic() - start < 3
    time.sleep(3.5)
    assert not marker.exists()


def test_child_env_excludes_secrets(monkeypatch):
    monkeypatch.setenv("TESTIO_TEACHER_API_KEY", "secret")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    env = build_child_env()
    assert "TESTIO_TEACHER_API_KEY" not in env
    assert "AWS_SECRET_ACCESS_KEY" not in env
    assert env.get("PATH") == os.environ.get("PATH")


def test_child_env_passthrough(monkeypatch):
    monkeypatch.setenv("MY_TOOLCHAIN_HOME", "/opt/tool")
    monkeypatch.setenv("TESTIO_PASSTHROUGH_ENV", "MY_TOOLCHAIN_HOME")
    assert build_child_env()["MY_TOOLCHAIN_HOME"] == "/opt/tool"


def test_missing_executable_raises_oserror():
    with pytest.raises(OSError):
        run_process(["definitely-not-a-real-binary-xyz"])
