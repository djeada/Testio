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

    elif script == "--flask":
        from apps.server.main import main as flask_main

        flask_main(sys.argv[2:])

    elif script == "--gui":
        from src.gui.main import main as gui_main

        gui_main(sys.argv[2:])


if __name__ == "__main__":
    main()
