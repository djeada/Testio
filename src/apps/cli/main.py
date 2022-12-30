"""
Main module. It is used to run the program.
"""

import sys

from src.apps.cli.result_renderer import ResultRenderer
from src.core.execution.data import (
    ExecutionManagerInputData,
    ExecutionManagerInputDataFactory,
)

sys.path.append(".")


from pathlib import Path
import argparse

from src.core.config_parser.parsers import ConfigParser
from src.core.execution.manager import ExecutionManager


class Parser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super(Parser, self).__init__(*args, **kwargs)
        self.add_argument("config_file", type=str, help="Path to config file")


def main(argv) -> None:
    """
    Parse command line arguments and run tests that are described in config file.
    Then create pdf report with test results. If there are no tests in config file,
    print error message.
    """
    # path = parse_command_line_args(sys.argv)
    argument_parser = Parser()
    args = argument_parser.parse_args(argv)
    path = Path(args.config_file)

    parser = ConfigParser()
    test_suite_config = parser.parse(path)
    execution_manager_data = ExecutionManagerInputDataFactory.from_test_suite_config(
        test_suite_config, path
    )
    renderer = ResultRenderer()

    for data in execution_manager_data:

        manager = ExecutionManager()
        result = manager.run(data)
        renderer.render(result)


if __name__ == "__main__":
    argv = sys.argv[1]
    # if argv is not list make it list
    if not isinstance(argv, list):
        argv = [argv]
    main(argv)
