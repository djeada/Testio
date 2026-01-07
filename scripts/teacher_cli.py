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

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.apps.cli.main import main


if __name__ == "__main__":
    # Run the main CLI with all commands available
    argv = sys.argv[1:]
    exit_code = main(argv)
    sys.exit(exit_code)
