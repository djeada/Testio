import argparse
import sys
from pathlib import Path

# Allow `python src/main.py ...` from a source checkout without installing.
_SRC_DIR = str(Path(__file__).resolve().parent)
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "script", type=str, choices=["cli", "fastapi"], help="Script to run"
    )
    args, extra_args = parser.parse_known_args()

    if args.script == "cli":
        from testio.apps.cli.main import main as cli_main

        return cli_main(extra_args)

    from testio.apps.server.main import main as fastapi_main

    return fastapi_main(extra_args) or 0


if __name__ == "__main__":
    sys.exit(main())
