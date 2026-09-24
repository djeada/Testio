"""
Data classes for execution module.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Union

from testio.core.config_parser.data import TestSuiteConfig
from testio.core.execution.command_utils import build_run_command

logger = logging.getLogger(__name__)


@dataclass
class ExecutionManagerInputData:
    """
    Input data for ExecutionManager.
    """

    command: str = ""
    input: List[str] = field(default_factory=list)
    output: List[str] = field(default_factory=list)
    timeout: int = 0
    use_regex: bool = False
    interleaved: bool = False
    unordered: bool = False
    # Set when the program could not be built; the test then fails with this
    # message instead of silently disappearing from the results.
    compile_error: str = ""
    # Working directory for the program under test; empty means the caller's
    # cwd. The server sets a throw-away per-request directory here.
    cwd: str = ""


@dataclass
class ExecutionInputData:
    """
    Input data for Runner.
    """

    command: str = ""
    input: str = ""
    timeout: int = 0
    cwd: str = ""


@dataclass
class ExecutionOutputData:
    """
    Output data from Runner.
    """

    stdout: str = ""
    stderr: str = ""
    timeout: bool = False
    # None means "unknown" (e.g. data built by hand); the comparator then
    # falls back to treating any stderr output as an execution error.
    returncode: Optional[int] = None
    output_truncated: bool = False


def as_lines(value: Union[str, List[str], None]) -> List[str]:
    """Normalise a config input/output value to a list of lines.

    A plain string is one block of text, so it is split on newlines rather
    than being iterated character by character.
    """
    if value is None:
        return []
    if isinstance(value, str):
        return value.split("\n") if value else []
    return [str(item) for item in value]


@dataclass
class ComparisonInputData:
    """
    Input data for OutputComparator.
    """

    input: str = ""
    expected_output: str = ""
    execution_output: ExecutionOutputData = field(default_factory=ExecutionOutputData)
    use_regex: bool = False
    unordered: bool = False


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

    def to_dict(self) -> Dict[str, Union[str, int]]:
        """
        Converts the object to a dictionary.
        :return: A dictionary representation of the object.
        """
        return {
            "input": self.input,
            "expected_output": self.expected_output,
            "output": self.output,
            "error": self.error,
            "result_name": self.result.name,
            "result": str(self.result),
        }


class ExecutionManagerFactory:
    @staticmethod
    def _compile_if_needed(
        test_suite_config: TestSuiteConfig,
        file_path: str,
        output_dir: Optional[str] = None,
    ) -> str:
        """
        Compiles the source file if compile_command is provided.

        :param test_suite_config: The TestSuiteConfig object containing compilation command
        :param file_path: Path to the source file
        :return: Path to the compiled executable or original path if no compilation
        :raises CompilationError: If compilation fails
        """
        if not test_suite_config.compile_command:
            return file_path

        from .compiler import Compiler

        compiler = Compiler()
        compiled_path = compiler.compile(
            test_suite_config.compile_command, file_path, output_dir=output_dir
        )
        return compiled_path if compiled_path else file_path

    @staticmethod
    def _compile_or_error(
        test_suite_config: TestSuiteConfig,
        file_path: str,
        output_dir: Optional[str] = None,
    ) -> "tuple[str, str]":
        from .compiler import CompilationError

        try:
            return (
                ExecutionManagerFactory._compile_if_needed(
                    test_suite_config, file_path, output_dir
                ),
                "",
            )
        except CompilationError as e:
            logger.info("Compilation failed for %s: %s", file_path, e)
            message = e.stderr.strip() or str(e)
            return file_path, f"Compilation failed:\n{message}"

    @staticmethod
    def _process_files(
        test_suite_config: TestSuiteConfig, path: str
    ) -> Dict[str, List[ExecutionManagerInputData]]:
        """
        Process files by compiling (if needed) and creating execution manager data.

        :param test_suite_config: The TestSuiteConfig object
        :param path: Path to file or directory to process
        :return: Dictionary mapping file paths to execution manager data lists
        """
        if Path(path).is_dir():
            file_data_dict = {}
            for file in sorted(Path(path).glob("*")):
                if file.is_file():
                    file_data_dict[str(file)] = ExecutionManagerFactory.build_for_file(
                        test_suite_config, str(file)
                    )
            return file_data_dict

        if not Path(path).is_file():
            return {}
        return {path: ExecutionManagerFactory.build_for_file(test_suite_config, path)}

    @staticmethod
    def build_for_file(
        test_suite_config: TestSuiteConfig,
        file_path: str,
        output_dir: Optional[str] = None,
    ) -> List[ExecutionManagerInputData]:
        """
        Compile ``file_path`` if the config requires it and build its test data.

        A compilation failure does not raise: every returned test carries the
        compiler message in ``compile_error`` and will be reported as failed.

        :param output_dir: Where compiled artifacts go (default: a private
            temporary directory removed at interpreter exit).
        """
        runnable_path, compile_error = ExecutionManagerFactory._compile_or_error(
            test_suite_config, file_path, output_dir
        )
        data_list = ExecutionManagerFactory.create_execution_manager_data(
            test_suite_config, runnable_path
        )
        for data in data_list:
            data.compile_error = compile_error
        return data_list

    @staticmethod
    def create_execution_manager_data(
        test_suite_config: TestSuiteConfig,
        path: str,
    ) -> List[ExecutionManagerInputData]:
        """
        Helper function that creates a list of ExecutionManagerInputData objects
        based on the provided TestSuiteConfig object and the path to the file
        being tested.
        """
        # Determine the command to use for running tests
        # Priority: run_command > command (for backward compatibility)
        if test_suite_config.run_command:
            # Use run_command if explicitly provided
            command = build_run_command(test_suite_config.run_command, path)
        elif test_suite_config.command:
            # Fall back to command for backward compatibility
            command = build_run_command(test_suite_config.command, path)
        else:
            # If neither is provided, just use the path (for compiled executables)
            command = build_run_command("", path)

        execution_manager_data_list = []
        for test_data in test_suite_config.tests:
            execution_manager_data = ExecutionManagerInputData(
                command=command,
                input=as_lines(test_data.input),
                output=as_lines(test_data.output),
                timeout=test_data.timeout,
                use_regex=test_data.use_regex,
                interleaved=test_data.interleaved,
                unordered=test_data.unordered,
            )
            execution_manager_data_list.append(execution_manager_data)
        return execution_manager_data_list

    @staticmethod
    def from_test_suite_config_local(
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
        path_obj = Path(test_suite_config.path)
        path = (
            str(Path(config_path).parent / path_obj)
            if not path_obj.is_absolute()
            else str(path_obj)
        )

        return ExecutionManagerFactory._process_files(test_suite_config, path)

    @staticmethod
    def from_test_suite_config_server(
        test_suite_config: TestSuiteConfig,
    ) -> Dict[str, List[ExecutionManagerInputData]]:
        """
        Creates a dictionary where the keys are paths to the tested files and the
        values are lists of ExecutionManagerInputData objects.

        :param test_suite_config: The TestSuiteConfig object.
        :return: A dictionary where the keys are paths to the tested files and the
                values are lists of ExecutionManagerInputData objects.
        """
        path_obj = Path(test_suite_config.path)
        path = (
            str(Path.cwd() / path_obj) if not path_obj.is_absolute() else str(path_obj)
        )
        return ExecutionManagerFactory._process_files(test_suite_config, path)
