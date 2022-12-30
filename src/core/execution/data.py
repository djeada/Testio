"""
Data classes for execution module.
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import List, Union


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


class ExecutionManagerInputDataFactory:
    """
    Alternative constructor for ExecutionManagerInputData.
    """
    @staticmethod
    def from_test_suite_config(
        test_suite_config, config_path
    ) -> List[ExecutionManagerInputData]:
        """
        Creates a list of ExecutionManagerInputData objects based on the
        provided TestSuiteConfig object.

        :param test_suite_config: The TestSuiteConfig object.
        :param config_path: The path to the configuration file.
        :return: A list of ExecutionManagerInputData objects.
        """
        path = test_suite_config.path

        if not Path(path).exists():
            path = str(Path(config_path).parent / path)

        command = f'{test_suite_config.command} "{path}"'.strip()

        return [
            ExecutionManagerInputData(
                command=command,
                input=test_data.input,
                output=test_data.output,
                timeout=test_data.timeout,
            )
            for test_data in test_suite_config.tests
        ]
