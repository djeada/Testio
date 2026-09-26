"""Tests for the student CLI command helpers."""

import argparse
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from testio.apps.cli.commands import student


def build_parser() -> argparse.ArgumentParser:
    """Create a parser with the student command registered."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    student.add_parser(subparsers)
    return parser


def test_student_check_accepts_javascript_aliases():
    """Test that JavaScript aliases are accepted by the parser."""
    parser = build_parser()

    js_args = parser.parse_args(
        [
            "student",
            "check",
            "solution.js",
            "--language",
            "javascript",
        ]
    )
    short_args = parser.parse_args(
        [
            "student",
            "check",
            "solution.js",
            "--language",
            "js",
        ]
    )

    assert js_args.language == "javascript"
    assert short_args.language == "js"


def test_check_syntax_uses_current_python_executable():
    """Test that Python syntax checks use the active interpreter."""
    file_path = Path("solution.py")

    with patch("subprocess.run") as run_mock:
        run_mock.return_value = subprocess.CompletedProcess([], 0, "", "")
        result = student.check_syntax(file_path, "python")

    run_mock.assert_called_once_with(
        [sys.executable, "-m", "py_compile", str(file_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result["valid"] is True


def test_check_syntax_supports_nodejs():
    """Test that Node.js syntax checking uses node --check."""
    file_path = Path("solution.js")

    with patch("subprocess.run") as run_mock:
        run_mock.return_value = subprocess.CompletedProcess([], 1, "", "SyntaxError")
        result = student.check_syntax(file_path, "nodejs")

    run_mock.assert_called_once_with(
        ["node", "--check", str(file_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result["valid"] is False
    assert result["errors"] == ["SyntaxError"]


def test_run_tests_compiles_c_submission(tmp_path):
    """`student test` must honour compile_command (C, C++, Rust, ...)."""
    import shutil

    import pytest

    from testio.apps.cli.commands.student import run_tests

    if shutil.which("gcc") is None:
        pytest.skip("gcc not available")

    source = tmp_path / "solution.c"
    source.write_text('#include <stdio.h>\nint main(){puts("hi");return 0;}\n')
    config = {
        "compile_command": "gcc {source} -o {output}",
        "path": "solution.c",
        "tests": [{"input": [], "output": ["hi"]}],
    }

    results = run_tests(source, config, tmp_path / "config.json")

    assert results["passed_tests"] == results["total_tests"] == 1
