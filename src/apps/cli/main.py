"""
Main module for the CLI application. 
You can start the application by using the main function.

The CLI supports multiple commands for different use cases:
- run: Execute tests from a configuration file
- validate: Validate configuration files and test cases
- batch: Test multiple student submissions in batch
- export: Export problems/configs to PDF, HTML, or Markdown
- generate: Generate configuration files interactively
- init: Initialize a new problem or homework structure
- student: Student-focused testing commands

For backward compatibility, passing a config file directly (without a command)
will run tests using the legacy interface.
"""

import sys

sys.path.append(".")

import argparse
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from typing import Tuple, List, Optional

from src.apps.cli.result_renderer import ResultRenderer
from src.core.config_parser.parsers import ConfigParser
from src.core.execution.data import ComparisonResult, ExecutionManagerFactory, ExecutionManagerInputData, ComparisonOutputData
from src.core.execution.manager import ExecutionManager


# Legacy functionality kept for backward compatibility
class LegacyParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super(LegacyParser, self).__init__(*args, **kwargs)
        self.add_argument("config_file", type=str, help="Path to config file")


def process_file(args: Tuple[str, List[ExecutionManagerInputData]]) -> Tuple[str, List[ComparisonOutputData], int, int, float]:
    """
    Process a single file's tests and return the results.
    This function is designed to be used with ProcessPoolExecutor.
    
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
    passed_tests_ratio = passed_test / total_test * 100 if total_test > 0 else 0
    
    return path, results, total_test, passed_test, passed_tests_ratio


def run_legacy(argv: list) -> int:
    """
    Legacy execution mode - runs tests directly from a config file.
    Kept for backward compatibility.
    
    :param argv: Command line arguments.
    :return: Exit code.
    """
    argument_parser = LegacyParser()
    args = argument_parser.parse_args(argv)
    config_path = Path(args.config_file)

    if not config_path.exists():
        print(f"Error: Config file '{config_path}' not found.")
        return 1

    parser = ConfigParser()
    try:
        test_suite_config = parser.parse_from_path(config_path)
    except Exception as e:
        print(f"Error: Failed to parse config file: {e}")
        return 1

    path_to_execution_manager_data = (
        ExecutionManagerFactory.from_test_suite_config_local(
            test_suite_config, str(config_path)
        )
    )
    
    if not path_to_execution_manager_data:
        print("Error: No files to test found.")
        return 1

    renderer = ResultRenderer()

    # Use ProcessPoolExecutor to run tests for multiple files concurrently
    with ProcessPoolExecutor() as executor:
        file_results = list(executor.map(process_file, path_to_execution_manager_data.items()))
    
    total_passed = 0
    total_tests = 0
    
    # Display results for each file
    for file_path, results, total_test, passed_test, passed_tests_ratio in file_results:
        total_tests += total_test
        total_passed += passed_test
        print(f"\nStarting tests for {file_path}")
        print(f"Correct tests: {passed_test}/{total_test} ({passed_tests_ratio:.2f}%)")
        for i, result in enumerate(results):
            renderer.render(result, i + 1)

    return 0 if total_passed == total_tests else 1


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="testio",
        description=(
            "Testio - A flexible testing framework for verifying program output.\n\n"
            "Use 'testio <command> --help' for more information on each command."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  testio run config.json                 Run tests from config file\n"
            "  testio validate config.json            Validate configuration\n"
            "  testio batch config.json submissions/  Batch test student submissions\n"
            "  testio export config.json -f html      Export as HTML\n"
            "  testio generate -t python              Generate Python config template\n"
            "  testio init homework1 -l python        Initialize new homework\n"
            "  testio student test my_code.py config.json  Student self-test\n"
        ),
    )
    
    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available commands",
        help="Command to run",
    )

    # Import and register all command modules
    from src.apps.cli.commands import run, validate, batch, export, generate, init, student

    run.add_parser(subparsers)
    validate.add_parser(subparsers)
    batch.add_parser(subparsers)
    export.add_parser(subparsers)
    generate.add_parser(subparsers)
    init.add_parser(subparsers)
    student.add_parser(subparsers)

    return parser


def main(argv: Optional[list] = None) -> int:
    """
    Main entry point for the CLI application.
    
    Supports both the new subcommand interface and legacy mode for backward compatibility.
    
    :param argv: Command line arguments (defaults to sys.argv[1:]).
    :return: Exit code.
    """
    if argv is None:
        argv = []
    
    # Check if first argument is a known command
    known_commands = {"run", "validate", "batch", "export", "generate", "init", "student", "-h", "--help"}
    
    if not argv or (argv and argv[0] not in known_commands):
        # Legacy mode: first argument is a config file path
        if argv and Path(argv[0]).suffix == ".json":
            print("(Using legacy mode. Consider using 'testio run <config>' instead.)")
            return run_legacy(argv)
        elif argv:
            # Try to parse as new command anyway
            pass
        else:
            # No arguments, show help
            pass
    
    # New subcommand interface
    parser = create_parser()
    args = parser.parse_args(argv)
    
    if not hasattr(args, "func") or args.func is None:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    argv = sys.argv[1:]
    exit_code = main(argv)
    sys.exit(exit_code)
