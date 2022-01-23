"""
This module defines Parser class.
"""

import json
import re
from pathlib import Path
from typing import List, Optional

from src.string_consts import (
    TEST_JSON,
    TEST_INPUT_JSON,
    TEST_OUTPUT_JSON,
    PROGRAM_PATH_JSON,
    TIMEOUT_JSON,
)


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
        self.path_to_exe = Path()
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
                self.path_to_exe = file_content[PROGRAM_PATH_JSON]
                self.timeout = file_content[TIMEOUT_JSON]
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
            if re.compile(TEST_JSON).match(key)
        ]
        self.tests = [
            Test(test_data[TEST_INPUT_JSON], test_data[TEST_OUTPUT_JSON])
            for test_data in tests_data
        ]

    @staticmethod
    def validate_config_file(file_content) -> None:
        """
        Validate the config file. Check if all required fields are present.
        """
        if PROGRAM_PATH_JSON not in file_content:
            raise ValueError(f"{PROGRAM_PATH_JSON} is not specified in config file!")

        if PROGRAM_PATH_JSON not in file_content:
            raise ValueError(f"{TIMEOUT_JSON} is not specified in config file!")

        tests_data = [
            file_content[key]
            for key in file_content
            if re.compile(TEST_JSON).match(key)
        ]

        if len(tests_data) == 0:
            raise ValueError("No tests are specified in config file!")

        for test in tests_data:
            if TEST_INPUT_JSON not in test:
                raise ValueError(
                    f"Test {test} does not contain required field {TEST_INPUT_JSON}!"
                )
            if TEST_OUTPUT_JSON not in test:
                raise ValueError(
                    f"Test {test} does not contain required field {TEST_OUTPUT_JSON}!"
                )
