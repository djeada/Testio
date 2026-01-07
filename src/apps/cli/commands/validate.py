"""
Validate command module - validates configuration files and test cases.
Teachers can use this to ensure their test configurations are correct.
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict, Any


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add the validate command parser to the subparsers."""
    parser = subparsers.add_parser(
        "validate",
        help="Validate configuration files and test cases",
        description="Validate JSON configuration files for correctness and completeness.",
    )
    parser.add_argument(
        "config_files",
        type=str,
        nargs="+",
        help="Path(s) to the JSON config file(s) to validate",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict validation (check for best practices)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to fix common issues and save corrected file",
    )
    parser.set_defaults(func=execute)


def validate_config(config_path: Path, strict: bool = False) -> Dict[str, Any]:
    """
    Validate a single configuration file.

    :param config_path: Path to the configuration file.
    :param strict: Whether to perform strict validation.
    :return: Dictionary with validation results.
    """
    result = {
        "file": str(config_path),
        "valid": True,
        "errors": [],
        "warnings": [],
        "info": [],
    }

    # Check file exists
    if not config_path.exists():
        result["valid"] = False
        result["errors"].append(f"File not found: {config_path}")
        return result

    # Check file extension
    if config_path.suffix.lower() != ".json":
        result["warnings"].append("File does not have .json extension")

    # Try to parse JSON
    try:
        with open(config_path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        result["valid"] = False
        result["errors"].append(f"Invalid JSON: {e}")
        return result
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"Error reading file: {e}")
        return result

    # Validate required fields
    has_command = "command" in data and data["command"]
    has_run_command = "run_command" in data and data["run_command"]
    has_compile_command = "compile_command" in data and data["compile_command"]

    if not (has_command or has_run_command or has_compile_command):
        result["valid"] = False
        result["errors"].append(
            "Missing execution command. Must have 'command', 'run_command', or 'compile_command'"
        )

    if "path" not in data or not data["path"]:
        result["valid"] = False
        result["errors"].append("Missing 'path' field - specify the program to test")

    if "tests" not in data or not isinstance(data["tests"], list):
        result["valid"] = False
        result["errors"].append("Missing 'tests' field - must be a list of test cases")
    elif len(data["tests"]) == 0:
        result["valid"] = False
        result["errors"].append("No test cases defined - add at least one test")
    else:
        # Validate each test case
        for i, test in enumerate(data["tests"], 1):
            test_errors = validate_test_case(test, i, strict)
            result["errors"].extend(test_errors["errors"])
            result["warnings"].extend(test_errors["warnings"])
            if test_errors["errors"]:
                result["valid"] = False

    # Check if path exists (as info, not error)
    if "path" in data and data["path"]:
        test_path = config_path.parent / data["path"]
        if not test_path.exists():
            result["warnings"].append(
                f"Target path '{data['path']}' not found relative to config file"
            )

    # Strict mode additional checks
    if strict:
        if has_command and has_run_command:
            result["warnings"].append(
                "Both 'command' and 'run_command' specified. 'run_command' takes precedence"
            )

        for i, test in enumerate(data.get("tests", []), 1):
            if test.get("timeout", 0) > 60:
                result["warnings"].append(
                    f"Test {i}: Long timeout ({test['timeout']}s) may indicate inefficient test"
                )
            if test.get("timeout", 0) < 1:
                result["warnings"].append(
                    f"Test {i}: Very short timeout may cause false negatives"
                )

    # Add info
    result["info"].append(f"Tests defined: {len(data.get('tests', []))}")
    if has_compile_command:
        result["info"].append("Uses compilation")
    if any(t.get("interleaved") for t in data.get("tests", [])):
        result["info"].append("Uses interleaved I/O testing")
    if any(t.get("unordered") for t in data.get("tests", [])):
        result["info"].append("Uses unordered output matching")
    if any(t.get("use_regex") for t in data.get("tests", [])):
        result["info"].append("Uses regex matching")

    return result


def validate_test_case(test: Dict[str, Any], index: int, strict: bool) -> Dict[str, List[str]]:
    """
    Validate a single test case.

    :param test: The test case dictionary.
    :param index: Test case number for error messages.
    :param strict: Whether to perform strict validation.
    :return: Dictionary with errors and warnings lists.
    """
    result = {"errors": [], "warnings": []}

    # Check required fields
    if "input" not in test:
        result["errors"].append(f"Test {index}: Missing 'input' field")
    if "output" not in test:
        result["errors"].append(f"Test {index}: Missing 'output' field")
    if "timeout" not in test:
        result["errors"].append(f"Test {index}: Missing 'timeout' field")
    elif not isinstance(test["timeout"], (int, float)) or test["timeout"] <= 0:
        result["errors"].append(f"Test {index}: 'timeout' must be a positive number")

    # Validate input format
    if "input" in test:
        inp = test["input"]
        if not isinstance(inp, (str, list)):
            result["errors"].append(f"Test {index}: 'input' must be a string or list")
        elif isinstance(inp, list) and not all(isinstance(x, str) for x in inp):
            result["errors"].append(f"Test {index}: 'input' list must contain only strings")

    # Validate output format
    if "output" in test:
        out = test["output"]
        if not isinstance(out, (str, list)):
            result["errors"].append(f"Test {index}: 'output' must be a string or list")
        elif isinstance(out, list) and not all(isinstance(x, str) for x in out):
            result["errors"].append(f"Test {index}: 'output' list must contain only strings")

    # Strict mode checks
    if strict:
        if "interleaved" in test and test["interleaved"]:
            inp = test.get("input", [])
            out = test.get("output", [])
            if isinstance(inp, str):
                inp = [inp] if inp else []
            if isinstance(out, str):
                out = [out] if out else []
            # For interleaved, output should generally be longer than input
            if len(out) < len(inp):
                result["warnings"].append(
                    f"Test {index}: Interleaved test has fewer outputs than inputs"
                )

    return result


def fix_config(config_path: Path) -> bool:
    """
    Attempt to fix common issues in a configuration file.

    :param config_path: Path to the configuration file.
    :return: True if fixes were made, False otherwise.
    """
    try:
        with open(config_path, "r") as f:
            data = json.load(f)
    except Exception:
        return False

    modified = False

    # Normalize input/output to lists
    for test in data.get("tests", []):
        if "input" in test and isinstance(test["input"], str):
            if test["input"]:
                test["input"] = [test["input"]]
            else:
                test["input"] = []
            modified = True
        if "output" in test and isinstance(test["output"], str):
            if test["output"]:
                test["output"] = [test["output"]]
            else:
                test["output"] = []
            modified = True

    # Add default timeout if missing
    for test in data.get("tests", []):
        if "timeout" not in test:
            test["timeout"] = 10
            modified = True

    if modified:
        with open(config_path, "w") as f:
            json.dump(data, f, indent=4)

    return modified


def execute(args: argparse.Namespace) -> int:
    """
    Execute the validate command.

    :param args: Parsed command line arguments.
    :return: Exit code (0 for success, non-zero for failure).
    """
    all_valid = True

    for config_file in args.config_files:
        config_path = Path(config_file)
        result = validate_config(config_path, args.strict)

        # Print results
        print(f"\n{'='*60}")
        print(f"Validating: {result['file']}")
        print(f"{'='*60}")

        if result["valid"]:
            print("✓ Configuration is valid")
        else:
            print("✗ Configuration has errors")
            all_valid = False

        # Print errors
        for error in result["errors"]:
            print(f"  ERROR: {error}")

        # Print warnings
        for warning in result["warnings"]:
            print(f"  WARNING: {warning}")

        # Print info
        for info in result["info"]:
            print(f"  INFO: {info}")

        # Attempt fixes if requested
        if args.fix and result["errors"]:
            print("\nAttempting to fix issues...")
            if fix_config(config_path):
                print("  Some issues were fixed. Please re-validate.")
            else:
                print("  Could not automatically fix issues.")

    print(f"\n{'='*60}")
    if all_valid:
        print("All configurations are valid!")
        return 0
    else:
        print("Some configurations have errors.")
        return 1
