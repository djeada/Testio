import argparse
import sys
from apps.cli.main import main as cli_main


def main():
    # Parse the first argument to determine which script to run
    script = sys.argv[1]

    # Pass the remaining arguments to the selected script
    if script == "--cli":
        from apps.cli.main import main as cli_main

        cli_main(sys.argv[2:])
    elif script == "flask":
        from src.flask_app import main as flask_main

        flask_main(sys.argv[2:])
    elif script == "qt":
        from src.qt_app import main as qt_main

        qt_main(sys.argv[2:])


if __name__ == "__main__":
    main()
