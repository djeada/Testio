"""
Main module. It is used to run the program.
"""

import sys
from pathlib import Path
from typing import List, Optional

from src.output_comparator import OutputComparator, TestResult
from src.parsers import ConfigParser
from src.program_output import ProgramOutput


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
    path_to_exe = (
        Path(parser.path_to_exe)
        if Path(parser.path_to_exe).is_absolute()
        else path.parents[0] / Path(parser.path_to_exe)
    )

    test_results = []

    for test in parser.tests:
        program_output = ProgramOutput(path_to_exe, test.input, parser.timeout)
        result_stdout = program_output.result.stdout
        result_stderr = program_output.result.stderr
        result_timeout = program_output.result.timeout
        test_results.append(
            TestResult(
                test.input, test.output, result_stdout, result_stderr, result_timeout
            )
        )

    output_comparator = OutputComparator(test_results, path_to_exe)
    output_comparator.display_test_results()
    output_comparator.generate_pdf_report()


if __name__ == "__main__":
    main()
