"""The published JSON schema must agree with the parser."""

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")

from testio.core.config_parser.parsers import validate_config_data  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads(
    (ROOT / "src" / "testio" / "schemas" / "testio-config.schema.json").read_text()
)
EXAMPLE_CONFIGS = sorted((ROOT / "examples").glob("*/*.json"))


def _schema_errors(data):
    return list(jsonschema.Draft202012Validator(SCHEMA).iter_errors(data))


@pytest.mark.parametrize(
    "path", EXAMPLE_CONFIGS, ids=lambda p: p.parent.name + "/" + p.name
)
def test_examples_are_schema_and_parser_valid(path):
    data = json.loads(path.read_text())
    assert _schema_errors(data) == []
    assert validate_config_data(data) == []


@pytest.mark.parametrize(
    "config",
    [
        {
            "command": "python3",
            "path": "p.py",
            "tests": [{"input": "a", "output": "a"}],
        },
        {"run_command": "node", "path": "p.js", "tests": []},
        {
            "compile_command": "gcc {source} -o {output}",
            "path": "p.c",
            "tests": [
                {"input": [], "output": [1, 2], "timeout": 0.5, "unordered": True}
            ],
        },
    ],
)
def test_valid_configs_accepted_by_both(config):
    assert _schema_errors(config) == []
    assert validate_config_data(config) == []


@pytest.mark.parametrize(
    "config",
    [
        {"path": "p.py", "tests": []},
        {"command": "python3", "tests": []},
        {"command": "python3", "path": "p.py", "tests": {}},
        {"command": "python3", "path": "p.py", "tests": [{"output": "x"}]},
        {
            "command": "python3",
            "path": "p.py",
            "tests": [{"input": "", "output": "", "timeout": 0}],
        },
        {
            "command": "python3",
            "path": "p.py",
            "tests": [{"input": "", "output": "", "use_regex": "yes"}],
        },
    ],
)
def test_invalid_configs_rejected_by_both(config):
    assert _schema_errors(config) != []
    assert validate_config_data(config) != []
