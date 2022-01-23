import sys
import os
from pathlib import Path
from typing import List, Optional

from src.misc import file_exists, get_leading_path, files_in_dir
from src.parsers import ConfigParser
from src.program_output import ProgramOutput
from src.string_consts import PROGRAM_PATH_JSON, TIMEOUT_JSON


def parse_command_line_args(args: List[str]) -> Optional[Path]:
    """
    Parses the command line arguments. The first argument is the path to the
    config file. If the config file is not found, the program exits.
    :param args: The command line arguments.
    :return: The path to the config file.
    """
    if len(args) == 2:
        path = Path(args[1])
        if path.is_file():
            return path

    raise Exception("You have to provide path to config file as an argument!")


def main() -> None:
    """
    Parse command line arguments and run tests that are described in config file.
    Then create pdf report with test results. If there are no tests in config file,
    print error message.
    """
    path = parse_command_line_args(sys.argv)
    parser = ConfigParser(path)
    ProgramOutput(parser.path_to_exe, parser.timeout, parser.tests, path)


if __name__ == "__main__":
    main()
