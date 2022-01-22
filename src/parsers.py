"""
This module defines Parser class.
"""

import json
import re
from typing import List, Dict, Tuple, Optional

from src.string_consts import TEST_JSON, TEST_INPUT_JSON, TEST_OUTPUT_JSON, PROGRAM_PATH_JSON, TIMEOUT_JSON


class Test:
    """
    Single test consiting of input and output data.
    Input and output data are lists of strings, but
    each of them can be empty.
    """
    def __init__(self, input, output):
        self._input = input
        self._output = output

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
        self.data = None
        self.tests = []
        self.read_config_file(path)
        self.validate_config_file()

    def read_config_file(self, path) -> None:
        """
        Read the config file and create a dictionary with all data.
        """
        try:
            with open(path) as f:
                self.data = json.load(f)
                self.parse_tests()

        except EnvironmentError:
            print("Failed to open config file")

    def parse_tests(self) -> None:
        """
        Parse tests from config file.
        """
        for key in self.data:
            if re.compile(TEST_JSON).match(key):
                test_data = self.data[key]
                if TEST_INPUT_JSON in test_data and TEST_OUTPUT_JSON in test_data:
                    input_data = test_data[TEST_INPUT_JSON]
                    output = test_data[TEST_OUTPUT_JSON]
                    self.tests.append(Test(input_data, output))

    def validate_config_file(self) -> None:
        """
        Validate the config file. Check if all required fields are present.
        """
        if PROGRAM_PATH_JSON not in self.data:
            raise Exception("{} not found in config file!".format(PROGRAM_PATH_JSON))

        if PROGRAM_PATH_JSON not in self.data:
            raise Exception("{} not found in config file!".format(TIMEOUT_JSON))

        if len(self.tests) == 0:
            raise Exception("no tests found in config file!")
