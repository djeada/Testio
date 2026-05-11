"""Tests for the CLI main entry point."""

from unittest.mock import patch

import pytest


def test_run_subcommand_dispatches(tmp_path):
    """The 'run' subcommand should be recognized without error."""
    from src.apps.cli.main import main

    program = tmp_path / "program.py"
    program.write_text("print('hi')")
    config = tmp_path / "config.json"
    config.write_text('{"command": "python3", "path": "program.py", "tests": []}')

    with patch("sys.argv", ["testio", "run", str(config)]):
        try:
            assert main(["run", str(config)]) == 0
        except SystemExit as error:
            assert error.code == 0 or error.code is None


def test_unknown_subcommand_exits_nonzero():
    """An unrecognized subcommand should exit with a non-zero code."""
    from src.apps.cli.main import main

    with pytest.raises(SystemExit) as exc_info:
        main(["not-a-real-command"])
    assert exc_info.value.code != 0


def test_legacy_mode_json_file(tmp_path):
    """Passing a .json file directly (legacy mode) should be recognized."""
    from src.apps.cli.main import main

    program = tmp_path / "program.py"
    program.write_text("print('hi')")
    config = tmp_path / "config.json"
    config.write_text('{"command": "python3", "path": "program.py", "tests": []}')

    try:
        assert main([str(config)]) == 0
    except SystemExit as error:
        assert error.code == 0 or error.code is None
