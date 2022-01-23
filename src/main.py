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
    path_to_exe = Path(parser.path_to_exe) if Path(parser.path_to_exe).is_absolute() else path.parents[0] / Path(parser.path_to_exe)

    for test in parser.tests:
        program_output = ProgramOutput(path_to_exe, test.input, parser.timeout)
        if program_output.result.stdout is not None:
            print(program_output.result.stdout)
        if program_output.result.stderr is not None:
            print(program_output.result.stderr)
        if program_output.result.timeout:
            print("Timeout!")


if __name__ == "__main__":
    main()
