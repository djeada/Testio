"""Tests for command vs run_command vs compile_command precedence."""

import json

from src.core.config_parser.parsers import ConfigParser


def _config(tmp_path, **kwargs):
    data = {"path": ".", "tests": [], **kwargs}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(data))
    return str(config_path)


def test_command_field_used(tmp_path):
    config_path = _config(tmp_path, command="python3")
    parser = ConfigParser()
    result = parser.parse_from_path(config_path)
    assert result.command == "python3"


def test_run_command_overrides_command(tmp_path):
    """run_command takes precedence over command for execution."""
    config_path = _config(tmp_path, command="python3", run_command="python3 -u")
    parser = ConfigParser()
    result = parser.parse_from_path(config_path)
    assert result.run_command == "python3 -u"


def test_compile_command_present(tmp_path):
    config_path = _config(
        tmp_path,
        compile_command="gcc {source} -o {output}",
        run_command="./prog",
    )
    parser = ConfigParser()
    result = parser.parse_from_path(config_path)
    assert result.compile_command == "gcc {source} -o {output}"
    assert result.run_command == "./prog"
