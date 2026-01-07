#!/usr/bin/env python3
"""
Entry point for the Student UI (web) application.
This is a student-focused version of the web interface with
limited features suitable for student code submission and testing.

For Nuitka compilation, this script serves as the main entry point.
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.apps.server.main import main


if __name__ == "__main__":
    # Run the server with student mode
    argv = sys.argv[1:]
    # Ensure student mode is set
    if "--mode" not in argv and "-m" not in argv:
        argv = ["--mode", "student"] + argv
    main(argv)
