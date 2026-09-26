"""
Parser for the JSON config file.
Gets the path to the config file as an input and returns
a Python representation of the config file as an output.


Example:

{
    "command": "python",
    "path": "path/to/script.py",
    "tests": [
        {
            "input": "input data",
            "output": "output data",
            "timeout": 10
        },
        {
            "input": [
                "input line 1",
                "input line 2"
            ],
            "output": [
                "output line 1",
                "output line 2"
            ],
            "timeout": 15
        }
    ]
}

becomes

TestSuiteConfig(
    command="python",
    path="path/to/script.py",
    tests=[
        TestData(
            input="input data",
            output="output data",
            timeout=10
        ),
        TestData(
            input=[
                "input line 1",
                "input line 2"
            ],
            output=[
                "output line 1",
                "output line 2"
            ],
            timeout=15
        )
    ]
)
"""

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Union

from testio.core.execution.command_utils import validate_command_template

from .data import TestData, TestSuiteConfig

DEFAULT_TIMEOUT_SECONDS = 5


def get_max_test_timeout() -> float:
    """Upper bound for a single test's timeout (TESTIO_MAX_TEST_TIMEOUT, seconds)."""
    return float(os.environ.get("TESTIO_MAX_TEST_TIMEOUT", "300"))


class ConfigNotParsable(ValueError):
    """Raised when a config file cannot be read or fails validation."""

    def __init__(self, reason: str = "") -> None:
        self.reason = reason
        message = "Config file is not parsable"
        super().__init__(f"{message}: {reason}" if reason else message)


@dataclass
class CONFIG_SCHEMA:
    """
    Class that represents the json schema for the config file.
    """

    COMMAND: str = "command"
    PATH: str = "path"
    TESTS: str = "tests"
    TEST_INPUT: str = "input"
    TEST_OUTPUT: str = "output"
    TIMEOUT: str = "timeout"
    USE_REGEX: str = "use_regex"
    INTERLEAVED: str = "interleaved"
    UNORDERED: str = "unordered"
    COMPILE_COMMAND: str = "compile_command"
    RUN_COMMAND: str = "run_command"


_COMMAND_FIELDS = (
    CONFIG_SCHEMA.COMMAND,
    CONFIG_SCHEMA.RUN_COMMAND,
    CONFIG_SCHEMA.COMPILE_COMMAND,
)
_FLAG_FIELDS = (
    CONFIG_SCHEMA.USE_REGEX,
    CONFIG_SCHEMA.INTERLEAVED,
    CONFIG_SCHEMA.UNORDERED,
)


def _is_text_block(value: Any) -> bool:
    """A str, or a list of scalar lines (numbers are accepted and stringified)."""
    if isinstance(value, str):
        return True
    return isinstance(value, list) and all(
        isinstance(item, (str, int, float)) and not isinstance(item, bool)
        for item in value
    )


def _normalise_text_block(value: Union[str, List[Any]]) -> Union[str, List[str]]:
    if isinstance(value, str):
        return value
    return [str(item) for item in value]


def validate_config_data(data: Any) -> List[str]:
    """Return a list of human-readable problems with a config; empty if valid."""
    if not isinstance(data, dict):
        return ["config must be a JSON object"]

    errors: List[str] = []

    has_command = False
    for field_name in _COMMAND_FIELDS:
        value = data.get(field_name)
        if value is None:
            continue
        if not isinstance(value, str):
            errors.append(f"'{field_name}' must be a string")
            continue
        has_command = True
        if value.strip():
            try:
                validate_command_template(value, field_name)
            except ValueError as exc:
                errors.append(str(exc))
    if not has_command:
        errors.append(
            "one of 'command', 'run_command' or 'compile_command' is required"
        )

    path = data.get(CONFIG_SCHEMA.PATH)
    if not isinstance(path, str) or not path.strip():
        errors.append("'path' is required and must be a non-empty string")

    tests = data.get(CONFIG_SCHEMA.TESTS)
    if not isinstance(tests, list):
        errors.append("'tests' is required and must be a list")
        return errors

    max_timeout = get_max_test_timeout()
    for index, test in enumerate(tests, start=1):
        where = f"tests[{index}]"
        if not isinstance(test, dict):
            errors.append(f"{where} must be an object")
            continue
        for field_name in (CONFIG_SCHEMA.TEST_INPUT, CONFIG_SCHEMA.TEST_OUTPUT):
            if field_name not in test:
                errors.append(f"{where}: '{field_name}' is required")
            elif not _is_text_block(test[field_name]):
                errors.append(
                    f"{where}: '{field_name}' must be a string or a list of strings"
                )
        timeout = test.get(CONFIG_SCHEMA.TIMEOUT, DEFAULT_TIMEOUT_SECONDS)
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout)
            or timeout <= 0
        ):
            errors.append(f"{where}: 'timeout' must be a positive number of seconds")
        elif timeout > max_timeout:
            errors.append(f"{where}: 'timeout' must not exceed {max_timeout:g} seconds")
        for flag in _FLAG_FIELDS:
            if flag in test and not isinstance(test[flag], bool):
                errors.append(f"{where}: '{flag}' must be true or false")

    return errors


class ConfigParser:
    def parse_from_path(self, path: Union[str, Path]) -> TestSuiteConfig:
        """Load and validate a config file.

        :raises ConfigNotParsable: with a message describing every problem found.
        """
        return self.parse_from_json(self._load(path))

    def parse_from_json(self, json_data: Any) -> TestSuiteConfig:
        """Validate an already-decoded config.

        :raises ConfigNotParsable: with a message describing every problem found.
        """
        errors = validate_config_data(json_data)
        if errors:
            raise ConfigNotParsable("; ".join(errors))

        tests = [
            TestData(
                input=_normalise_text_block(test[CONFIG_SCHEMA.TEST_INPUT]),
                output=_normalise_text_block(test[CONFIG_SCHEMA.TEST_OUTPUT]),
                timeout=test.get(CONFIG_SCHEMA.TIMEOUT, DEFAULT_TIMEOUT_SECONDS),
                use_regex=test.get(CONFIG_SCHEMA.USE_REGEX, False),
                interleaved=test.get(CONFIG_SCHEMA.INTERLEAVED, False),
                unordered=test.get(CONFIG_SCHEMA.UNORDERED, False),
            )
            for test in json_data[CONFIG_SCHEMA.TESTS]
        ]

        return TestSuiteConfig(
            command=(json_data.get(CONFIG_SCHEMA.COMMAND) or "").strip(),
            path=json_data[CONFIG_SCHEMA.PATH],
            tests=tests,
            compile_command=(
                json_data.get(CONFIG_SCHEMA.COMPILE_COMMAND) or ""
            ).strip(),
            run_command=(json_data.get(CONFIG_SCHEMA.RUN_COMMAND) or "").strip(),
        )

    def validate(self, path: Union[str, Path]) -> bool:
        try:
            return not validate_config_data(self._load(path))
        except ConfigNotParsable:
            return False

    @staticmethod
    def _load(path: Union[str, Path]) -> Any:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as exc:
            raise ConfigNotParsable(f"invalid JSON: {exc}") from exc
        except OSError as exc:
            raise ConfigNotParsable(f"cannot read {path}: {exc.strerror}") from exc
