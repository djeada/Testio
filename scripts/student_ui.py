#!/usr/bin/env python3
"""
Entry point for the Student UI (web) application.
This is a student-focused version of the web interface with
limited features suitable for student code submission and testing.

For Nuitka compilation, this script serves as the main entry point.
"""

import sys
from pathlib import Path

# Make the `testio` package importable from a source checkout.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from testio.apps.server.main import main

if __name__ == "__main__":
    # Run the server with student mode
    argv = sys.argv[1:]
    # Ensure student mode is set
    if not any(arg == "--mode" or arg.startswith("--mode=") for arg in argv):
        argv = ["--mode", "student"] + argv
    main(argv)
