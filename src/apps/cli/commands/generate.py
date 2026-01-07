"""
Generate command module - interactively generate configuration files.
Teachers can use this to create test configurations easily.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add the generate command parser to the subparsers."""
    parser = subparsers.add_parser(
        "generate",
        help="Generate a configuration file interactively or from templates",
        description="Create test configuration files through interactive prompts or templates.",
    )
    parser.add_argument(
        "output",
        type=str,
        nargs="?",
        default="config.json",
        help="Output file path for the configuration (default: config.json)",
    )
    parser.add_argument(
        "--template",
        "-t",
        type=str,
        choices=["python", "c", "cpp", "java", "nodejs", "ruby", "go", "rust", "custom"],
        default="python",
        help="Language template to use (default: python)",
    )
    parser.add_argument(
        "--non-interactive",
        "-n",
        action="store_true",
        help="Generate a template without interactive prompts",
    )
    parser.add_argument(
        "--program",
        "-p",
        type=str,
        help="Path to the program to test",
    )
    parser.set_defaults(func=execute)


# Language templates
LANGUAGE_TEMPLATES = {
    "python": {
        "command": "python3",
        "extension": ".py",
        "description": "Python 3",
    },
    "c": {
        "compile_command": "gcc {source} -o {output}",
        "extension": ".c",
        "description": "C (GCC)",
    },
    "cpp": {
        "compile_command": "g++ {source} -o {output}",
        "extension": ".cpp",
        "description": "C++ (G++)",
    },
    "java": {
        "compile_command": "javac {source}",
        "run_command": "java",
        "extension": ".java",
        "description": "Java",
    },
    "nodejs": {
        "run_command": "node",
        "extension": ".js",
        "description": "Node.js",
    },
    "ruby": {
        "run_command": "ruby",
        "extension": ".rb",
        "description": "Ruby",
    },
    "go": {
        "compile_command": "go build -o {output} {source}",
        "extension": ".go",
        "description": "Go",
    },
    "rust": {
        "compile_command": "rustc {source} -o {output}",
        "extension": ".rs",
        "description": "Rust",
    },
    "custom": {
        "command": "",
        "extension": "",
        "description": "Custom language",
    },
}


def prompt(message: str, default: Optional[str] = None) -> str:
    """Prompt user for input with optional default value."""
    if default:
        result = input(f"{message} [{default}]: ").strip()
        return result if result else default
    return input(f"{message}: ").strip()


def prompt_yes_no(message: str, default: bool = True) -> bool:
    """Prompt user for yes/no answer."""
    default_str = "Y/n" if default else "y/N"
    result = input(f"{message} [{default_str}]: ").strip().lower()
    if not result:
        return default
    return result in ("y", "yes", "true", "1")


def prompt_list(message: str) -> List[str]:
    """Prompt user for multiple lines of input."""
    print(f"{message} (enter empty line to finish):")
    lines = []
    while True:
        line = input("  > ")
        if not line:
            break
        lines.append(line)
    return lines


def create_test_case_interactive() -> Dict[str, Any]:
    """Interactively create a single test case."""
    print("\n--- New Test Case ---")

    # Get input
    print("Enter test input (one line per input, empty line to finish):")
    inputs = []
    while True:
        line = input("  input> ")
        if not line:
            break
        inputs.append(line)

    # Get expected output
    print("Enter expected output (one line per output, empty line to finish):")
    outputs = []
    while True:
        line = input("  output> ")
        if not line:
            break
        outputs.append(line)

    # Get timeout
    timeout_str = prompt("Timeout in seconds", "10")
    try:
        timeout = int(timeout_str)
    except ValueError:
        timeout = 10

    # Advanced options
    test_case = {
        "input": inputs,
        "output": outputs,
        "timeout": timeout,
    }

    if prompt_yes_no("Configure advanced options?", False):
        if prompt_yes_no("Is this an interactive (interleaved I/O) test?", False):
            test_case["interleaved"] = True
        if prompt_yes_no("Should output order be ignored?", False):
            test_case["unordered"] = True
        if prompt_yes_no("Use regex matching for output?", False):
            test_case["use_regex"] = True

    return test_case


def generate_interactive(template_name: str, output_path: Path, program_path: Optional[str]) -> Dict[str, Any]:
    """Generate configuration through interactive prompts."""
    template = LANGUAGE_TEMPLATES.get(template_name, LANGUAGE_TEMPLATES["python"])

    print("\n" + "=" * 50)
    print("Testio Configuration Generator")
    print("=" * 50)
    print(f"Template: {template['description']}")
    print()

    config: Dict[str, Any] = {}

    # Program path
    if program_path:
        config["path"] = program_path
    else:
        default_program = f"program{template.get('extension', '')}"
        config["path"] = prompt("Path to the program to test", default_program)

    # Language-specific configuration
    if template.get("command"):
        cmd = prompt("Execution command", template["command"])
        if cmd:
            config["command"] = cmd

    if template.get("run_command"):
        run_cmd = prompt("Run command", template["run_command"])
        if run_cmd:
            config["run_command"] = run_cmd

    if template.get("compile_command"):
        compile_cmd = prompt("Compile command", template["compile_command"])
        if compile_cmd:
            config["compile_command"] = compile_cmd

    # Test cases
    config["tests"] = []
    print("\n--- Test Cases ---")
    print("Let's add some test cases.")

    while True:
        test_case = create_test_case_interactive()
        config["tests"].append(test_case)
        print(f"Test case {len(config['tests'])} added.")

        if not prompt_yes_no("Add another test case?", True):
            break

    return config


def generate_template(template_name: str, program_path: Optional[str]) -> Dict[str, Any]:
    """Generate a template configuration without interactive prompts."""
    template = LANGUAGE_TEMPLATES.get(template_name, LANGUAGE_TEMPLATES["python"])

    config: Dict[str, Any] = {}

    # Set path
    if program_path:
        config["path"] = program_path
    else:
        config["path"] = f"program{template.get('extension', '.py')}"

    # Language-specific configuration
    if template.get("command"):
        config["command"] = template["command"]
    if template.get("run_command"):
        config["run_command"] = template["run_command"]
    if template.get("compile_command"):
        config["compile_command"] = template["compile_command"]

    # Sample test cases
    config["tests"] = [
        {
            "input": ["sample input"],
            "output": ["expected output"],
            "timeout": 10
        },
        {
            "input": [],
            "output": ["Hello World"],
            "timeout": 5
        }
    ]

    return config


def execute(args: argparse.Namespace) -> int:
    """
    Execute the generate command.

    :param args: Parsed command line arguments.
    :return: Exit code (0 for success, non-zero for failure).
    """
    output_path = Path(args.output)

    # Check if output file exists
    if output_path.exists():
        if not args.non_interactive:
            if not prompt_yes_no(f"'{output_path}' already exists. Overwrite?", False):
                print("Aborted.")
                return 1
        else:
            print(f"Warning: Overwriting existing file '{output_path}'")

    # Generate configuration
    if args.non_interactive:
        config = generate_template(args.template, args.program)
        print(f"Generated template configuration using '{args.template}' template.")
    else:
        try:
            config = generate_interactive(args.template, output_path, args.program)
        except KeyboardInterrupt:
            print("\nAborted.")
            return 1
        except EOFError:
            print("\nInput ended unexpectedly.")
            return 1

    # Save configuration
    with open(output_path, "w") as f:
        json.dump(config, f, indent=4)

    print(f"\nConfiguration saved to: {output_path}")
    print(f"Tests defined: {len(config['tests'])}")
    print("\nYou can now run tests with:")
    print(f"  python src/main.py cli run {output_path}")

    return 0
