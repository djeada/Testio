"""
This module is the entry point of the application.
It sets up the `TestioServer` application, parses the command-line arguments, and updates the execution manager data if
a config file is provided.

The server can be started in two modes:
- teacher (default): Full access to all features including exam management, homework grading, and config generation
- student: Limited access focused on code submission and testing
"""
import argparse
import sys
from typing import List, Optional

sys.path.append(".")

from src.apps.server.app.testio_server import create_app
from src.apps.server.database.configuration_data import update_execution_manager_data
from src.core.config_parser.parsers import ConfigParser
from src.core.execution.data import ExecutionManagerFactory


class ArgumentParser(argparse.ArgumentParser):
    """
    Custom argument parser class that adds the `config_file` argument.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_argument(
            "config_file", type=str, help="Path to config file", nargs="?"
        )
        self.add_argument(
            "--host", type=str, default="127.0.0.1", help="Host to bind the server to"
        )
        self.add_argument(
            "--port", type=int, default=5000, help="Port to bind the server to"
        )
        self.add_argument(
            "--mode",
            type=str,
            choices=["teacher", "student"],
            default="teacher",
            help="Application mode: 'teacher' (default) for full access, 'student' for student-focused UI"
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

    # Create app with the specified mode
    app = create_app(mode=args.mode)

    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
