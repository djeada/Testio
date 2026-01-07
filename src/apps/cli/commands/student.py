"""
Student command module - student-focused testing functionality.
Students can use this to test their submissions before submitting.
"""

import argparse
import json
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any
from concurrent.futures import ProcessPoolExecutor

from src.core.config_parser.parsers import ConfigParser
from src.core.execution.data import (
    ComparisonResult,
    ExecutionManagerFactory,
    ExecutionManagerInputData,
    ComparisonOutputData,
)
from src.core.execution.manager import ExecutionManager


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add the student command parser to the subparsers."""
    parser = subparsers.add_parser(
        "student",
        help="Student-focused testing commands",
        description="Commands for students to test their code submissions.",
    )

    # Create subcommands for student
    student_subparsers = parser.add_subparsers(
        dest="student_command",
        help="Student commands",
    )

    # Test command
    test_parser = student_subparsers.add_parser(
        "test",
        help="Test your submission against the test cases",
    )
    test_parser.add_argument(
        "submission",
        type=str,
        help="Path to your submission file",
    )
    test_parser.add_argument(
        "config_file",
        type=str,
        help="Path to the test configuration file",
    )
    test_parser.add_argument(
        "--show-expected",
        action="store_true",
        help="Show expected output (if available)",
    )
    test_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output for each test",
    )
    test_parser.set_defaults(func=execute_test)

    # Check command
    check_parser = student_subparsers.add_parser(
        "check",
        help="Quick syntax/compilation check without running tests",
    )
    check_parser.add_argument(
        "submission",
        type=str,
        help="Path to your submission file",
    )
    check_parser.add_argument(
        "--language",
        "-l",
        type=str,
        choices=["python", "c", "cpp", "java", "go", "rust"],
        help="Programming language (auto-detected if not specified)",
    )
    check_parser.set_defaults(func=execute_check)

    # Practice command
    practice_parser = student_subparsers.add_parser(
        "practice",
        help="Interactive practice mode with immediate feedback",
    )
    practice_parser.add_argument(
        "config_file",
        type=str,
        help="Path to the test configuration file",
    )
    practice_parser.set_defaults(func=execute_practice)

    parser.set_defaults(func=lambda args: parser.print_help())


def detect_language(file_path: Path) -> Optional[str]:
    """Detect programming language from file extension."""
    extension_map = {
        ".py": "python",
        ".c": "c",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".java": "java",
        ".js": "nodejs",
        ".rb": "ruby",
        ".go": "go",
        ".rs": "rust",
    }
    return extension_map.get(file_path.suffix.lower())


def check_syntax(file_path: Path, language: str) -> Dict[str, Any]:
    """
    Check syntax/compilation of a file.
    
    :param file_path: Path to the source file.
    :param language: Programming language.
    :return: Dictionary with check results.
    """
    import subprocess

    result = {
        "valid": True,
        "language": language,
        "errors": [],
        "warnings": [],
    }

    try:
        if language == "python":
            # Use py_compile for Python
            proc = subprocess.run(
                ["python3", "-m", "py_compile", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if proc.returncode != 0:
                result["valid"] = False
                result["errors"].append(proc.stderr.strip())

        elif language == "c":
            # Syntax check only with gcc
            proc = subprocess.run(
                ["gcc", "-fsyntax-only", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if proc.returncode != 0:
                result["valid"] = False
                result["errors"].append(proc.stderr.strip())

        elif language == "cpp":
            proc = subprocess.run(
                ["g++", "-fsyntax-only", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if proc.returncode != 0:
                result["valid"] = False
                result["errors"].append(proc.stderr.strip())

        elif language == "java":
            # Compile to check syntax
            proc = subprocess.run(
                ["javac", "-d", tempfile.gettempdir(), str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if proc.returncode != 0:
                result["valid"] = False
                result["errors"].append(proc.stderr.strip())

        elif language == "go":
            proc = subprocess.run(
                ["go", "build", "-o", "/dev/null", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if proc.returncode != 0:
                result["valid"] = False
                result["errors"].append(proc.stderr.strip())

        elif language == "rust":
            proc = subprocess.run(
                ["rustc", "--emit=metadata", "-o", "/dev/null", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if proc.returncode != 0:
                result["valid"] = False
                result["errors"].append(proc.stderr.strip())

        else:
            result["warnings"].append(f"Syntax checking not supported for {language}")

    except subprocess.TimeoutExpired:
        result["valid"] = False
        result["errors"].append("Compilation/syntax check timed out")
    except FileNotFoundError as e:
        result["warnings"].append(f"Compiler not found: {e}")
    except Exception as e:
        result["errors"].append(f"Error during check: {e}")

    return result


def run_tests(
    submission_path: Path,
    config: dict,
    config_path: Path,
    show_expected: bool = False,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Run tests on a student submission.
    
    :param submission_path: Path to the student's submission.
    :param config: Test configuration dictionary.
    :param config_path: Path to the config file.
    :param show_expected: Whether to show expected output.
    :param verbose: Whether to show detailed output.
    :return: Test results dictionary.
    """
    parser = ConfigParser()
    test_suite_config = parser.parse_from_json(config)

    # Create execution manager data using the student's file
    execution_data = ExecutionManagerFactory._create_execution_manager_data(
        test_suite_config, str(submission_path)
    )

    manager = ExecutionManager()
    results = []

    for data in execution_data:
        result = manager.run(data)
        results.append(result)

    total_tests = len(results)
    passed_tests = len(
        [r for r in results if r.result == ComparisonResult.MATCH]
    )
    score = (passed_tests / total_tests * 100) if total_tests > 0 else 0

    return {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": total_tests - passed_tests,
        "score": round(score, 2),
        "test_results": [
            {
                "index": i + 1,
                "passed": r.result == ComparisonResult.MATCH,
                "result_type": str(r.result),
                "input": r.input,
                "expected_output": r.expected_output if show_expected else None,
                "actual_output": r.output,
                "error": r.error,
            }
            for i, r in enumerate(results)
        ],
    }


def execute_test(args: argparse.Namespace) -> int:
    """Execute the student test command."""
    submission_path = Path(args.submission)
    config_path = Path(args.config_file)

    if not submission_path.exists():
        print(f"Error: Submission file '{submission_path}' not found.")
        return 1

    if not config_path.exists():
        print(f"Error: Config file '{config_path}' not found.")
        return 1

    print("=" * 50)
    print("TESTIO - Student Test Mode")
    print("=" * 50)
    print(f"Testing: {submission_path.name}")
    print()

    # Load config
    try:
        with open(config_path) as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error: Failed to load config: {e}")
        return 1

    # Run tests
    print("Running tests...")
    results = run_tests(
        submission_path,
        config,
        config_path,
        show_expected=args.show_expected,
        verbose=args.verbose,
    )

    # Display results
    print()
    print("-" * 50)
    print(f"Score: {results['score']:.1f}%")
    print(f"Passed: {results['passed_tests']}/{results['total_tests']}")
    print("-" * 50)

    for test in results["test_results"]:
        status = "✓ PASS" if test["passed"] else "✗ FAIL"
        print(f"\nTest {test['index']}: {status}")

        if args.verbose or not test["passed"]:
            if test["input"]:
                print(f"  Input: {test['input'][:100]}...")

            if test["error"]:
                print(f"  Error: {test['error']}")
            elif not test["passed"]:
                print(f"  Your output: {test['actual_output'][:100] if test['actual_output'] else '(none)'}...")
                if args.show_expected and test["expected_output"]:
                    print(f"  Expected: {test['expected_output'][:100]}...")

    print()
    if results["passed_tests"] == results["total_tests"]:
        print("🎉 All tests passed! Great job!")
        return 0
    else:
        print(f"Keep trying! {results['failed_tests']} test(s) still failing.")
        return 1


def execute_check(args: argparse.Namespace) -> int:
    """Execute the student check command."""
    submission_path = Path(args.submission)

    if not submission_path.exists():
        print(f"Error: File '{submission_path}' not found.")
        return 1

    # Detect language
    language = args.language or detect_language(submission_path)
    if not language:
        print(f"Error: Could not detect language. Please specify with --language")
        return 1

    print("=" * 50)
    print("TESTIO - Syntax Check")
    print("=" * 50)
    print(f"File: {submission_path.name}")
    print(f"Language: {language}")
    print()

    # Run syntax check
    result = check_syntax(submission_path, language)

    if result["valid"]:
        print("✓ Syntax check passed!")
        if result["warnings"]:
            for warning in result["warnings"]:
                print(f"  Warning: {warning}")
        return 0
    else:
        print("✗ Syntax check failed!")
        for error in result["errors"]:
            print(f"\n{error}")
        return 1


def execute_practice(args: argparse.Namespace) -> int:
    """Execute the student practice command."""
    config_path = Path(args.config_file)

    if not config_path.exists():
        print(f"Error: Config file '{config_path}' not found.")
        return 1

    # Load config
    try:
        with open(config_path) as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error: Failed to load config: {e}")
        return 1

    print("=" * 50)
    print("TESTIO - Practice Mode")
    print("=" * 50)
    print(f"Problem: {config_path.stem}")
    print(f"Test cases: {len(config.get('tests', []))}")
    print()

    # Show test case information
    print("Available test cases:")
    for i, test in enumerate(config.get("tests", []), 1):
        inp = test.get("input", [])
        if isinstance(inp, str):
            inp = [inp] if inp else []
        timeout = test.get("timeout", "N/A")
        print(f"  Test {i}: {len(inp)} input(s), {timeout}s timeout")

    print()
    print("To test your solution, use:")
    print(f"  python src/main.py cli student test <your_file> {config_path}")
    print()
    print("Tips:")
    print("  - Use '--show-expected' to see expected output when tests fail")
    print("  - Use '--verbose' for detailed output on all tests")

    return 0
