#!/usr/bin/env python3
"""
Entry point for the Student CLI application.
This is a student-focused version of the CLI that provides
limited commands suitable for student self-testing.

For Nuitka compilation, this script serves as the main entry point.
"""

import sys
from pathlib import Path

# Make the `testio` package importable from a source checkout.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from testio.apps.cli.main import main

STUDENT_SUBCOMMANDS = {"test", "check", "practice"}


def build_argv(argv: list) -> list:
    """Map student-CLI arguments onto the full CLI's `student` command.

    Only student commands are exposed: `student_cli prog.py config.json`
    is shorthand for `testio student test prog.py config.json`.
    """
    if not argv or argv[0] in ("-h", "--help"):
        return ["student", "--help"]
    if argv[0] == "--version":
        return ["--version"]
    if argv[0] in STUDENT_SUBCOMMANDS:
        return ["student"] + argv
    return ["student", "test"] + argv


if __name__ == "__main__":
    sys.exit(main(build_argv(sys.argv[1:])))
