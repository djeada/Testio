#!/usr/bin/env python3
"""
Entry point for the Teacher CLI application.
This is the full-featured version of the CLI with all commands
available for instructors including batch grading, validation,
and configuration management.

For Nuitka compilation, this script serves as the main entry point.
"""

import sys
from pathlib import Path

# Make the `testio` package importable from a source checkout.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from testio.apps.cli.main import main

if __name__ == "__main__":
    # Run the main CLI with all commands available
    argv = sys.argv[1:]
    exit_code = main(argv)
    sys.exit(exit_code)
