#!/usr/bin/env python3
"""
Entry point for the Teacher UI (web) application.
This is the full-featured version of the web interface with
all features available for instructors including exam management,
homework grading, and configuration generation.

For Nuitka compilation, this script serves as the main entry point.
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.apps.server.main import main


if __name__ == "__main__":
    # Run the server with teacher mode (default)
    argv = sys.argv[1:]
    # Ensure teacher mode is set
    if "--mode" not in argv and "-m" not in argv:
        argv = ["--mode", "teacher"] + argv
    main(argv)
