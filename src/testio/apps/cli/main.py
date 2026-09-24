"""
Main module for the CLI application.
You can start the application by using the main function.

The CLI supports multiple commands for different use cases:
- run: Execute tests from a configuration file
- validate: Validate configuration files and test cases
- batch: Test multiple student submissions in batch
- export: Export problems/configs to PDF, HTML, or Markdown
- generate: Generate configuration files interactively
- init: Initialize a new problem or homework structure
- student: Student-focused testing commands

For backward compatibility, passing a config file directly (without a command)
will run tests using the legacy interface.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from testio import __version__
from testio.apps.cli.commands import run as run_command
from testio.apps.cli.commands.run import process_file  # noqa: F401 (re-export)


# Legacy functionality kept for backward compatibility.
# NOTE: This path is only reachable when the first argument ends with ".json".
# Passing a non-JSON file without a subcommand falls through to the new parser,
# which will print a usage error. This is intentional — legacy mode is JSON-only.
class LegacyParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super(LegacyParser, self).__init__(*args, **kwargs)
        self.add_argument("config_file", type=str, help="Path to config file")


def run_legacy(argv: list) -> int:
    """
    Legacy execution mode - runs tests directly from a config file.
    Kept for backward compatibility; equivalent to ``testio run <config>``.

    :param argv: Command line arguments.
    :return: Exit code.
    """
    args = LegacyParser().parse_args(argv)
    return run_command.execute(
        argparse.Namespace(
            config_file=args.config_file,
            report=False,
            output=None,
            quiet=False,
            format="console",
        )
    )


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="testio",
        description=(
            "Testio - A flexible testing framework for verifying program output.\n\n"
            "Use 'testio <command> --help' for more information on each command."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  testio run config.json                 Run tests from config file\n"
            "  testio validate config.json            Validate configuration\n"
            "  testio batch config.json submissions/  Batch test student submissions\n"
            "  testio export config.json -f html      Export as HTML\n"
            "  testio generate -t python              Generate Python config template\n"
            "  testio init homework1 -l python        Initialize new homework\n"
            "  testio student test my_code.py config.json  Student self-test\n"
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available commands",
        help="Command to run",
    )

    # Import and register all command modules
    from testio.apps.cli.commands import (
        batch,
        export,
        generate,
        init,
        run,
        student,
        validate,
    )

    run.add_parser(subparsers)
    validate.add_parser(subparsers)
    batch.add_parser(subparsers)
    export.add_parser(subparsers)
    generate.add_parser(subparsers)
    init.add_parser(subparsers)
    student.add_parser(subparsers)

    return parser


def main(argv: Optional[list] = None) -> int:
    """
    Main entry point for the CLI application.

    Supports both the new subcommand interface and legacy mode for backward compatibility.

    :param argv: Command line arguments (defaults to sys.argv[1:]).
    :return: Exit code.
    """
    if argv is None:
        argv = sys.argv[1:]

    # Legacy mode: `testio config.json` behaves like `testio run config.json`.
    if argv and Path(argv[0]).suffix == ".json":
        print(
            "(Using legacy mode. Consider using 'testio run <config>' instead.)",
            file=sys.stderr,
        )
        return run_legacy(argv)

    # New subcommand interface
    parser = create_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func") or args.func is None:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
