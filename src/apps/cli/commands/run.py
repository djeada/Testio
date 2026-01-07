"""
Run command module - executes tests from a config file.
This is the original CLI functionality refactored as a command.
"""

import argparse
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from typing import Tuple, List

from src.apps.cli.result_renderer import ResultRenderer
from src.core.config_parser.parsers import ConfigParser
from src.core.execution.data import (
    ComparisonResult,
    ExecutionManagerFactory,
    ExecutionManagerInputData,
    ComparisonOutputData,
)
from src.core.execution.manager import ExecutionManager


def process_file(
    args: Tuple[str, List[ExecutionManagerInputData]]
) -> Tuple[str, List[ComparisonOutputData], int, int, float]:
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


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add the run command parser to the subparsers."""
    parser = subparsers.add_parser(
        "run",
        help="Run tests from a configuration file",
        description="Execute tests defined in a JSON configuration file against program(s).",
    )
    parser.add_argument("config_file", type=str, help="Path to the JSON config file")
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate a report file (JSON format)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file path for the report",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress detailed output, only show summary",
    )
    parser.set_defaults(func=execute)


def execute(args: argparse.Namespace) -> int:
    """
    Execute the run command.

    :param args: Parsed command line arguments.
    :return: Exit code (0 for success, non-zero for failure).
    """
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

    path_to_execution_manager_data = ExecutionManagerFactory.from_test_suite_config_local(
        test_suite_config, str(config_path)
    )

    if not path_to_execution_manager_data:
        print("Error: No files to test found.")
        return 1

    renderer = ResultRenderer()

    # Use ProcessPoolExecutor to run tests for multiple files concurrently
    with ProcessPoolExecutor() as executor:
        file_results = list(
            executor.map(process_file, path_to_execution_manager_data.items())
        )

    # Track overall results
    total_files = len(file_results)
    total_tests = 0
    total_passed = 0
    all_results = []

    # Display results for each file
    for path, results, test_count, passed_count, passed_ratio in file_results:
        total_tests += test_count
        total_passed += passed_count

        if not args.quiet:
            print(f"\n{'='*60}")
            print(f"Tests for: {path}")
            print(f"{'='*60}")
            print(f"Results: {passed_count}/{test_count} ({passed_ratio:.2f}%)")

            for i, result in enumerate(results):
                renderer.render(result, i + 1)

        all_results.append({
            "file": path,
            "total_tests": test_count,
            "passed_tests": passed_count,
            "pass_rate": passed_ratio,
            "tests": [result.to_dict() for result in results],
        })

    # Print summary
    overall_ratio = (total_passed / total_tests * 100) if total_tests > 0 else 0
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Files tested: {total_files}")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_tests - total_passed}")
    print(f"Overall pass rate: {overall_ratio:.2f}%")

    # Generate report if requested
    if args.report:
        import json
        from datetime import datetime

        report = {
            "generated_at": datetime.now().isoformat(),
            "config_file": str(config_path),
            "summary": {
                "files_tested": total_files,
                "total_tests": total_tests,
                "passed": total_passed,
                "failed": total_tests - total_passed,
                "pass_rate": overall_ratio,
            },
            "results": all_results,
        }

        output_path = args.output or f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to: {output_path}")

    # Return non-zero if any tests failed
    return 0 if total_passed == total_tests else 1
