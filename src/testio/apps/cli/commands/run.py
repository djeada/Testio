"""
Run command module - executes tests from a config file.
This is the original CLI functionality refactored as a command.
"""

import argparse
import sys
import uuid
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import List, Tuple

from testio.apps.cli.result_renderer import (
    ResultRenderer,
    render_json_report,
    render_junitxml_report,
    render_tap_report,
)
from testio.core.config_parser.parsers import ConfigNotParsable, ConfigParser
from testio.core.execution.data import (
    ComparisonOutputData,
    ComparisonResult,
    ExecutionManagerFactory,
    ExecutionManagerInputData,
)
from testio.core.execution.manager import ExecutionManager


def process_file(
    args: Tuple[str, List[ExecutionManagerInputData]],
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
    parser.add_argument(
        "--format",
        "-f",
        choices=["console", "json", "junitxml", "tap"],
        default="console",
        metavar="FORMAT",
        help=(
            "Output format: console (default), json, junitxml, tap. "
            "Non-console formats write to stdout or -o/--output."
        ),
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
        print(f"Error: Config file '{config_path}' not found.", file=sys.stderr)
        return 1

    parser = ConfigParser()
    try:
        test_suite_config = parser.parse_from_path(config_path)
    except ConfigNotParsable as e:
        print(f"Error: Invalid config '{config_path}': {e.reason}", file=sys.stderr)
        return 1

    if not test_suite_config.tests:
        print(f"Error: '{config_path}' defines no tests.", file=sys.stderr)
        return 1

    target = Path(test_suite_config.path)
    if not target.is_absolute():
        target = config_path.parent / target
    if not target.exists():
        print(
            f"Error: Program path '{test_suite_config.path}' not found "
            f"(resolved to '{target}').",
            file=sys.stderr,
        )
        return 1

    path_to_execution_manager_data = (
        ExecutionManagerFactory.from_test_suite_config_local(
            test_suite_config, str(config_path)
        )
    )

    if not path_to_execution_manager_data:
        print(f"Error: No files to test found in '{target}'.", file=sys.stderr)
        return 1

    fmt = getattr(args, "format", "console")
    renderer = ResultRenderer()

    # Use ProcessPoolExecutor to run tests for multiple files concurrently
    with ProcessPoolExecutor() as executor:
        file_results = list(
            executor.map(process_file, path_to_execution_manager_data.items())
        )

    # Collect results
    total_files = len(file_results)
    total_tests = 0
    total_passed = 0
    all_results = []

    for path, results, test_count, passed_count, passed_ratio in file_results:
        total_tests += test_count
        total_passed += passed_count

        # Console per-file output (skipped for machine-readable formats)
        if fmt == "console" and not args.quiet:
            print(f"\n{'='*60}")
            print(f"Tests for: {path}")
            print(f"{'='*60}")
            print(f"Results: {passed_count}/{test_count} ({passed_ratio:.2f}%)")
            for i, result in enumerate(results):
                renderer.render(result, i + 1)

        all_results.append(
            {
                "file": path,
                "total_tests": test_count,
                "passed_tests": passed_count,
                "pass_rate": passed_ratio,
                "tests": [result.to_dict() for result in results],
            }
        )

    overall_ratio = (total_passed / total_tests * 100) if total_tests > 0 else 0
    summary = {
        "config_file": str(config_path),
        "files_tested": total_files,
        "total_tests": total_tests,
        "passed": total_passed,
        "failed": total_tests - total_passed,
        "pass_rate": overall_ratio,
    }

    if fmt == "console":
        # Human-readable summary
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Files tested: {total_files}")
        print(f"Total tests:  {total_tests}")
        print(f"Passed:       {total_passed}")
        print(f"Failed:       {total_tests - total_passed}")
        print(f"Pass rate:    {overall_ratio:.2f}%")

        # --report (or -o in console mode) saves JSON alongside console output
        if args.report or args.output:
            import json
            from datetime import datetime

            report = {
                "generated_at": datetime.now().isoformat(),
                **summary,
                "results": all_results,
            }
            output_path = args.output or f"report_{uuid.uuid4().hex[:8]}.json"
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\nReport saved to: {output_path}")
    else:
        # Machine-readable output
        _FORMATTERS = {
            "json": render_json_report,
            "junitxml": render_junitxml_report,
            "tap": render_tap_report,
        }
        formatted = _FORMATTERS[fmt](all_results, summary)
        if args.output:
            with open(args.output, "w") as f:
                f.write(formatted)
                f.write("\n")
        else:
            print(formatted)

    return 0 if total_passed == total_tests else 1
