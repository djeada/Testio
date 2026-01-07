#!/usr/bin/env python3
"""
Entry point for the Student CLI application.
This is a student-focused version of the CLI that provides
limited commands suitable for student self-testing.

For Nuitka compilation, this script serves as the main entry point.
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.apps.cli.main import main


if __name__ == "__main__":
    # Run the main CLI with student-focused command
    argv = sys.argv[1:]
    # If no command is specified, default to student subcommand
    if argv and argv[0] not in {"student", "-h", "--help"}:
        # Prepend 'student' command for student-focused experience
        argv = ["student"] + argv
    exit_code = main(argv)
    sys.exit(exit_code)
