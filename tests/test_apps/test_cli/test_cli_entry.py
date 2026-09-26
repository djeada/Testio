"""Tests for the CLI main entry point."""

from unittest.mock import patch

import pytest


def test_run_subcommand_dispatches(tmp_path):
    """The 'run' subcommand should be recognized without error."""
    from testio.apps.cli.main import main

    program = tmp_path / "program.py"
    program.write_text("print('hi')")
    config = tmp_path / "config.json"
    config.write_text(
        '{"command": "python3", "path": "program.py", "tests": [{"input": [], "output": ["hi"]}]}'
    )

    with patch("sys.argv", ["testio", "run", str(config)]):
        try:
            assert main(["run", str(config)]) == 0
        except SystemExit as error:
            assert error.code == 0 or error.code is None


def test_unknown_subcommand_exits_nonzero():
    """An unrecognized subcommand should exit with a non-zero code."""
    from testio.apps.cli.main import main

    with pytest.raises(SystemExit) as exc_info:
        main(["not-a-real-command"])
    assert exc_info.value.code != 0


def test_legacy_mode_json_file(tmp_path):
    """Passing a .json file directly (legacy mode) should be recognized."""
    from testio.apps.cli.main import main

    program = tmp_path / "program.py"
    program.write_text("print('hi')")
    config = tmp_path / "config.json"
    config.write_text(
        '{"command": "python3", "path": "program.py", "tests": [{"input": [], "output": ["hi"]}]}'
    )

    try:
        assert main([str(config)]) == 0
    except SystemExit as error:
        assert error.code == 0 or error.code is None


def _write_suite(tmp_path, program_source, tests, **extra):
    import json

    (tmp_path / "program.py").write_text(program_source)
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {"command": "python3", "path": "program.py", "tests": tests, **extra}
        )
    )
    return config


def test_console_script_reads_sys_argv(tmp_path):
    """The installed `testio` script calls main() without argv."""
    from testio.apps.cli.main import main

    config = _write_suite(tmp_path, "print('hi')", [{"input": [], "output": ["bye"]}])
    with patch("sys.argv", ["testio", "run", str(config)]):
        assert main() == 1


def test_failing_suite_exits_nonzero(tmp_path):
    from testio.apps.cli.main import main

    config = _write_suite(tmp_path, "print('hi')", [{"input": [], "output": ["bye"]}])
    assert main(["run", str(config), "-q"]) == 1


def test_empty_suite_is_an_error(tmp_path):
    from testio.apps.cli.main import main

    config = _write_suite(tmp_path, "print('hi')", [])
    assert main(["run", str(config)]) == 1


def test_missing_program_is_an_error(tmp_path, capsys):
    from testio.apps.cli.main import main

    config = _write_suite(tmp_path, "", [{"input": [], "output": [""]}])
    (tmp_path / "program.py").unlink()
    assert main(["run", str(config)]) == 1
    assert "not found" in capsys.readouterr().err


def test_invalid_config_reports_reason(tmp_path, capsys):
    from testio.apps.cli.main import main

    config = tmp_path / "config.json"
    config.write_text('{"command": "python3", "path": "p.py", "tests": {"a": 1}}')
    assert main(["run", str(config)]) == 1
    assert "'tests' is required and must be a list" in capsys.readouterr().err


def test_string_input_and_output_are_lines_not_characters(tmp_path):
    from testio.apps.cli.main import main

    config = _write_suite(
        tmp_path, "print(input())", [{"input": "hello", "output": "hello"}]
    )
    assert main(["run", str(config), "-q"]) == 0


def test_nonzero_exit_fails_even_with_matching_output(tmp_path):
    from testio.apps.cli.main import main

    config = _write_suite(
        tmp_path,
        "import sys; print('hi'); sys.exit(3)",
        [{"input": [], "output": ["hi"]}],
    )
    assert main(["run", str(config), "-q"]) == 1


def test_warnings_on_stderr_do_not_fail_a_passing_program(tmp_path):
    from testio.apps.cli.main import main

    config = _write_suite(
        tmp_path,
        "import sys; print('warn', file=sys.stderr); print('hi')",
        [{"input": [], "output": ["hi"]}],
    )
    assert main(["run", str(config), "-q"]) == 0


def test_src_main_propagates_exit_code(tmp_path):
    import subprocess
    import sys
    from pathlib import Path

    config = _write_suite(tmp_path, "print('hi')", [{"input": [], "output": ["bye"]}])
    entry = Path(__file__).resolve().parents[3] / "src" / "main.py"
    result = subprocess.run(
        [sys.executable, str(entry), "cli", "run", str(config), "-q"],
        capture_output=True,
    )
    assert result.returncode == 1
