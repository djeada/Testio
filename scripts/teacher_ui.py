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

# Make the `testio` package importable from a source checkout.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from testio.apps.server.main import main

if __name__ == "__main__":
    # Run the server with teacher mode (default)
    argv = sys.argv[1:]
    # Ensure teacher mode is set
    if not any(arg == "--mode" or arg.startswith("--mode=") for arg in argv):
        argv = ["--mode", "teacher"] + argv
    main(argv)
