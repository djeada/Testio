"""
Main module for the CLI application. 
You can start the application by using the main function.
"""

import sys

sys.path.append(".")

import argparse
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from typing import Tuple, List

from src.apps.cli.result_renderer import ResultRenderer
from src.core.config_parser.parsers import ConfigParser
from src.core.execution.data import ComparisonResult, ExecutionManagerFactory, ExecutionManagerInputData, ComparisonOutputData
from src.core.execution.manager import ExecutionManager


class Parser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super(Parser, self).__init__(*args, **kwargs)
        self.add_argument("config_file", type=str, help="Path to config file")


def process_file(args: Tuple[str, List[ExecutionManagerInputData]]) -> Tuple[str, List[ComparisonOutputData], int, int, float]:
    """
    Process a single file's tests and return the results.
    This function is designed to be used with multiprocessing.Pool.
    
    :param args: A tuple containing (path, execution_manager_data)
    :return: A tuple containing (path, results, total_test, passed_test, passed_tests_ratio)
    """
    path, execution_manager_data = args
    manager = ExecutionManager()
    results = []
    
    for data in execution_manager_data:
        result = manager.run(data)
        results.append(result)
    
    total_test = len(results)
    passed_test = len(
        [result for result in results if result.result == ComparisonResult.MATCH]
    )
    passed_tests_ratio = passed_test / total_test * 100
    
    return path, results, total_test, passed_test, passed_tests_ratio


def main(argv: list) -> None:
    """
    Parses the command line arguments and starts the execution manager.
    :param argv: Command line arguments.
    :return: None
    """
    argument_parser = Parser()
    args = argument_parser.parse_args(argv)
    path = Path(args.config_file)

    parser = ConfigParser()
    test_suite_config = parser.parse_from_path(path)
    path_to_execution_manager_data = (
        ExecutionManagerFactory.from_test_suite_config_local(
            test_suite_config, str(path)
        )
    )
    renderer = ResultRenderer()

    # Use ProcessPoolExecutor to run tests for multiple files concurrently
    with ProcessPoolExecutor() as executor:
        file_results = list(executor.map(process_file, path_to_execution_manager_data.items()))
    
    # Display results for each file
    for path, results, total_test, passed_test, passed_tests_ratio in file_results:
        print(f"\nStarting tests for {path}")
        print(f"Correct tests: {passed_test}/{total_test} ({passed_tests_ratio:.2f}%)")
        for i, result in enumerate(results):
            renderer.render(result, i + 1)


if __name__ == "__main__":
    argv = sys.argv[1]
    # if argv is not list make it list
    if not isinstance(argv, list):
        argv = [argv]
    main(argv)
