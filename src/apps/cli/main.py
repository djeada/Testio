"""
Main module for the CLI application. 
You can start the application by using the main function.
"""

import sys

sys.path.append(".")

from src.apps.cli.result_renderer import ResultRenderer
from src.core.execution.data import (
    ExecutionManagerFactory,
    ComparisonResult,
)


from pathlib import Path
import argparse

from src.core.config_parser.parsers import ConfigParser
from src.core.execution.manager import ExecutionManager


class Parser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super(Parser, self).__init__(*args, **kwargs)
        self.add_argument("config_file", type=str, help="Path to config file")


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
        ExecutionManagerFactory.from_test_suite_config_local(test_suite_config, path)
    )
    renderer = ResultRenderer()
    manager = ExecutionManager()

    for path, execution_manager_data in path_to_execution_manager_data.items():

        print(f"\nStarting tests for {path}")
        results = []

        for data in execution_manager_data:
            result = manager.run(data)
            results.append(result)

        total_test = len(results)
        passed_test = len(
            [result for result in results if result.result == ComparisonResult.MATCH]
        )
        passed_tests_ratio = passed_test / total_test * 100

        print(f"Correct tests: {passed_test}/{total_test} ({passed_tests_ratio:.2f}%)")
        for i, result in enumerate(results):
            renderer.render(result, i + 1)


if __name__ == "__main__":
    argv = sys.argv[1]
    # if argv is not list make it list
    if not isinstance(argv, list):
        argv = [argv]
    main(argv)
