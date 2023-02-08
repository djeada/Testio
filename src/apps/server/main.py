"""
This module is the entry point of the application.
It sets up the `TestioServer` application, parses the command-line arguments, and updates the execution manager data if
a config file is provided.
"""
import argparse
import sys
from typing import List, Optional

sys.path.append(".")

from src.apps.server.app.testio_server import TestioServer
from src.apps.server.database.configuration_data import update_execution_manager_data
from src.core.config_parser.parsers import ConfigParser
from src.core.execution.data import ExecutionManagerFactory

app = TestioServer(__name__)
app.debug = True


class ArgumentParser(argparse.ArgumentParser):
    """
    Custom argument parser class that adds the `config_file` argument.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_argument(
            "config_file", type=str, help="Path to config file", nargs="?"
        )


def main(argv: Optional[List[str]] = None):
    """
    The main function of the script.

    :param argv: List of command-line arguments. Defaults to `sys.argv[1:]`.
    """
    if argv is None:
        argv = sys.argv[1:]

    argument_parser = ArgumentParser()
    args = argument_parser.parse_args(argv)
    if args.config_file:
        path = args.config_file
        parser = ConfigParser()
        test_suite_config = parser.parse_from_path(path)
        execution_manager_data = ExecutionManagerFactory.from_test_suite_config_server(
            test_suite_config
        )
        update_execution_manager_data(execution_manager_data)

    app.run()


if __name__ == "__main__":
    main()
