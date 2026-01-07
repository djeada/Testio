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
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .data import TestData, TestSuiteConfig


class ConfigNotParsable(Exception):
    def __init__(self) -> None:
        super().__init__("Config file is not parsable")


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


class ConfigParser:
    def __init__(self) -> None:
        pass

    def parse_from_path(self, path: Path) -> TestSuiteConfig:

        if not self.validate(path):
            raise ConfigNotParsable()

        with open(path, "r") as f:
            data: dict = json.load(f)

        return self.parse_from_json(data)

    def parse_from_json(self, json_data: dict) -> Optional[TestSuiteConfig]:
        command = json_data.get(CONFIG_SCHEMA.COMMAND, "")
        path = json_data.get(CONFIG_SCHEMA.PATH)
        compile_command = json_data.get(CONFIG_SCHEMA.COMPILE_COMMAND, "")
        run_command = json_data.get(CONFIG_SCHEMA.RUN_COMMAND, "")

        tests = []
        for test_data in json_data.get(CONFIG_SCHEMA.TESTS, []):
            input_data = test_data.get(CONFIG_SCHEMA.TEST_INPUT)
            output_data = test_data.get(CONFIG_SCHEMA.TEST_OUTPUT)
            timeout = test_data.get(CONFIG_SCHEMA.TIMEOUT)
            use_regex = test_data.get(CONFIG_SCHEMA.USE_REGEX, False)
            interleaved = test_data.get(CONFIG_SCHEMA.INTERLEAVED, False)
            unordered = test_data.get(CONFIG_SCHEMA.UNORDERED, False)
            if input_data is None or output_data is None or timeout is None:
                return None

            tests.append(TestData(input_data, output_data, timeout, use_regex, interleaved, unordered))

        return TestSuiteConfig(
            command=command, 
            path=path, 
            tests=tests,
            compile_command=compile_command,
            run_command=run_command
        )

    def validate(self, path: Path) -> bool:

        with open(path, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return False

        # check if at least one of command, run_command, or compile_command is present
        # and that path and tests are present
        has_command = data.get(CONFIG_SCHEMA.COMMAND) is not None
        has_run_command = data.get(CONFIG_SCHEMA.RUN_COMMAND) is not None
        has_compile_command = data.get(CONFIG_SCHEMA.COMPILE_COMMAND) is not None
        
        if (
            not (has_command or has_run_command or has_compile_command)
            or data.get(CONFIG_SCHEMA.PATH) is None
            or data.get(CONFIG_SCHEMA.TESTS) is None
        ):
            return False

        # check if each test has input, output and timeout
        for test_data in data.get(CONFIG_SCHEMA.TESTS, []):
            if (
                test_data.get(CONFIG_SCHEMA.TEST_INPUT) is None
                or test_data.get(CONFIG_SCHEMA.TEST_OUTPUT) is None
                or test_data.get(CONFIG_SCHEMA.TIMEOUT) is None
            ):
                return False

        return True
