import sys
import os

from src.misc import file_exists, get_leading_path, files_in_dir
from src.parsers import ConfigParser
from src.program_output import ProgramOutput
from src.string_consts import PROGRAM_PATH_JSON, TIMEOUT_JSON


def parse_command_line_args(args) -> str:
    """
    Parses the command line arguments. The first argument is the path to the
    config file. If the config file is not found, the program exits.
    :param args: The command line arguments.
    :return: The path to the config file.
    """
    if len(args) > 1:
        path = args[1]
        if file_exists(path):
            return path

    else:
        raise Exception("You have to provide path to config file as an argument!")


def main() -> None:
    """
    Parse command line arguments and run tests that are described in config file.
    Then create pdf report with test results. If there are no tests in config file,
    print error message.
    """
    path = parse_command_line_args(sys.argv)
    leading_path = get_leading_path(path)
    parser = ConfigParser(path)
    data = parser.data
    path = data[PROGRAM_PATH_JSON]
    timeout = data[TIMEOUT_JSON]

    if os.path.isdir(os.path.join(leading_path, path)):
        for _file in files_in_dir(os.path.join(leading_path, path)):
            ProgramOutput(
                _file, timeout, parser.tests, os.path.join(leading_path, path)
            )

    else:
        ProgramOutput(path, timeout, parser.tests, leading_path)


if __name__ == "__main__":
    main()
