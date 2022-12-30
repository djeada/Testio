"""
Data classes for execution module.
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import List, Union, Dict

from src.core.config_parser.data import TestSuiteConfig


@dataclass
class ExecutionManagerInputData:
    """
    Input data for ExecutionManager.
    """

    command: str = ""
    input: List[str] = field(default_factory=list)
    output: List[str] = field(default_factory=list)
    timeout: int = 0


@dataclass
class ExecutionInputData:
    """
    Input data for Runner.
    """

    command: str = ""
    input: str = ""
    timeout: int = 0


@dataclass
class ExecutionOutputData:
    """
    Output data from Runner.
    """

    stdout: str = ""
    stderr: str = ""
    timeout: bool = False


@dataclass
class ComparisonInputData:
    """
    Input data for OutputComparator.
    """

    input: str = ""
    expected_output: str = ""
    execution_output: ExecutionOutputData = ExecutionOutputData()


class ComparisonResult(Enum):
    """
    Possible results of the comparison.
    """

    MATCH = auto()
    MISMATCH = auto()
    EXECUTION_ERROR = auto()
    TIMEOUT = auto()


@dataclass
class ComparisonOutputData:
    """
    Output data from OutputComparator.
    """

    input: str = ""
    expected_output: str = ""
    output: str = ""
    error: str = ""
    result: ComparisonResult = ComparisonResult.MISMATCH


class ExecutionManagerFactory:
    @staticmethod
    def _create_execution_manager_data(
        test_suite_config: TestSuiteConfig,
        path: str,
    ) -> List[ExecutionManagerInputData]:
        """
        Helper function that creates a list of ExecutionManagerInputData objects
        based on the provided TestSuiteConfig object and the path to the file
        being tested.
        """
        command = f'{test_suite_config.command} "{path}"'.strip()
        execution_manager_data_list = []
        for test_data in test_suite_config.tests:
            execution_manager_data = ExecutionManagerInputData(
                command=command,
                input=test_data.input,
                output=test_data.output,
                timeout=test_data.timeout,
            )
            execution_manager_data_list.append(execution_manager_data)
        return execution_manager_data_list

    @staticmethod
    def from_test_suite_config(
        test_suite_config: TestSuiteConfig, config_path: str
    ) -> Dict[str, List[ExecutionManagerInputData]]:
        """
        Creates a dictionary where the keys are paths to the tested files and the
        values are lists of ExecutionManagerInputData objects.

        :param test_suite_config: The TestSuiteConfig object.
        :param config_path: The path to the configuration file.
        :return: A dictionary where the keys are paths to the tested files and the
                values are lists of ExecutionManagerInputData objects.
        """
        path = test_suite_config.path
        path = str(Path(config_path).parent / path)

        if Path(path).is_dir():
            # path points to a folder
            file_data_dict = {}
            for file in Path(path).glob("*"):
                execution_manager_data_list = (
                    ExecutionManagerFactory._create_execution_manager_data(
                        test_suite_config, file
                    )
                )
                file_data_dict[file] = execution_manager_data_list
            return file_data_dict
        else:
            # path points to a file
            execution_manager_data_list = (
                ExecutionManagerFactory._create_execution_manager_data(
                    test_suite_config, path
                )
            )
            return {path: execution_manager_data_list}
