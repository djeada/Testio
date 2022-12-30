"""
This module defines Parser class for parsing config file.
"""

import json
import re
from pathlib import Path
from typing import List, Optional

from src.core.string_consts import CONFIG_SCHEMA


class Test:
    """
    Single test consisting of input and output data.
    Input and output data are lists of strings, but
    each of them can be empty.
    """

    def __init__(
            self, test_input: Optional[List[str]], test_output: Optional[List[str]]
    ):
        self._input = test_input
        self._output = test_output

    @property
    def input(self) -> Optional[List[str]]:
        """
        :return: Input data.
        """
        if not self._input:
            return ""

        string = "".join(elem + "\n" for elem in self._input)
        return string[:-1]

    @input.setter
    def input(self, value: List[str]) -> None:
        """
        :param value: Input data.
        :return: None
        """
        self._input = value

    @property
    def output(self) -> Optional[List[str]]:
        """
        :return: Output data.
        """
        if not self._output:
            return ""

        string = "".join(elem + "\n" for elem in self._output)
        return string[:-1]

    @output.setter
    def output(self, value: List[str]) -> None:
        """
        :param value: Output data.
        :return: None
        """
        self._output = value


class ConfigParser:
    """
    Parser used for parsing config file
    and creating tests from it.
    """

    def __init__(self, path):
        self.paths = Path()
        self.timeout = None
        self.tests = []
        self.read_config_file(path)

    def read_config_file(self, path) -> None:
        """
        Read the config file and create a dictionary with all data.
        """
        try:
            with open(path) as file_obj:
                file_content = json.load(file_obj)
                self.validate_config_file(file_content)
                self.timeout = file_content[CONFIG_SCHEMA.TIMEOUT_JSON]
                self.parse_path(file_content, path.parent)
                self.parse_tests(file_content)

        except OSError:
            print("Failed to open config file")

    def parse_tests(self, file_content) -> None:
        """
        Parse tests from config file.
        """
        tests_data = [
            file_content[key]
            for key in file_content
            if re.compile(CONFIG_SCHEMA.TEST_JSON).match(key)
        ]
        self.tests = [
            Test(test_data[CONFIG_SCHEMA.TEST_INPUT_JSON], test_data[CONFIG_SCHEMA.TEST_OUTPUT_JSON])
            for test_data in tests_data
        ]

    def parse_path(self, file_content: str, path_to_config: Path) -> None:
        """
        Parse path to executable from config file.
        If path is relative, it is considered relative to config file.
        If path is absolute, it is considered absolute.
        If path is given as a glob pattern, it is considered relative to config file.
        """
        if (path_to_config / file_content[CONFIG_SCHEMA.PROGRAM_PATH_JSON]).is_file():
            self.paths = [path_to_config / file_content[CONFIG_SCHEMA.PROGRAM_PATH_JSON]]
            return

        elif Path(file_content[CONFIG_SCHEMA.PROGRAM_PATH_JSON]).is_file():
            self.paths = [Path(file_content[CONFIG_SCHEMA.PROGRAM_PATH_JSON])]
            return

        elif "*" in file_content[CONFIG_SCHEMA.PROGRAM_PATH_JSON]:
            # check if there exists a file with the same name as the glob pattern
            glob_pattern = file_content[CONFIG_SCHEMA.PROGRAM_PATH_JSON]
            matches = list(path_to_config.rglob(glob_pattern))
            if len(matches) > 0:
                self.paths = matches
                return

        raise Exception("Invalid path to executable")

    @staticmethod
    def validate_config_file(file_content) -> None:
        """
        Validate the config file. Check if all required fields are present.
        """
        if CONFIG_SCHEMA.PROGRAM_PATH_JSON not in file_content:
            raise ValueError(f"{CONFIG_SCHEMA.PROGRAM_PATH_JSON} is not specified in config file!")

        if CONFIG_SCHEMA.PROGRAM_PATH_JSON not in file_content:
            raise ValueError(f"{CONFIG_SCHEMA.TIMEOUT_JSON} is not specified in config file!")

        tests_data = [
            file_content[key]
            for key in file_content
            if re.compile(CONFIG_SCHEMA.TEST_JSON).match(key)
        ]

        if len(tests_data) == 0:
            raise ValueError("No tests are specified in config file!")

        for test in tests_data:
            if CONFIG_SCHEMA.TEST_INPUT_JSON not in test:
                raise ValueError(
                    f"Test {test} does not contain required field {CONFIG_SCHEMA.TEST_INPUT_JSON}!"
                )
            if CONFIG_SCHEMA.TEST_OUTPUT_JSON not in test:
                raise ValueError(
                    f"Test {test} does not contain required field {CONFIG_SCHEMA.TEST_OUTPUT_JSON}!"
                )
