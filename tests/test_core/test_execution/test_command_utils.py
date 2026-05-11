"""Tests for command utility helpers."""

import pytest

from src.core.execution.command_utils import (
    build_run_command,
    infer_source_suffix,
    replace_command_path,
    split_command,
    validate_command_template,
)


def test_validate_command_template_rejects_unknown_executable():
    with pytest.raises(ValueError):
        validate_command_template("evil-runner --flag", field_name="run_command")


def test_split_command_preserves_quoted_arguments():
    assert split_command('python3 -c "print(123)"') == ["python3", "-c", "print(123)"]


def test_build_run_command_quotes_paths_with_spaces():
    command = build_run_command("python3", "/tmp/program with spaces.py")
    assert split_command(command) == ["python3", "/tmp/program with spaces.py"]


def test_replace_command_path_swaps_only_program_token():
    updated = replace_command_path(
        'python3 "/tmp/original.py"',
        "/tmp/original.py",
        "/tmp/new path.py",
    )
    assert split_command(updated) == ["python3", "/tmp/new path.py"]


def test_infer_source_suffix_prefers_filename_suffix():
    assert infer_source_suffix(filename="solution.js", command="python3") == ".js"


def test_infer_source_suffix_falls_back_to_command():
    assert infer_source_suffix(command="node") == ".js"
