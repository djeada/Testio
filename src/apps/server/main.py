import sys
from pathlib import Path
from typing import List, Optional

from flask import Flask, render_template
from src.core.execution.comparator import OutputComparator, TestResult
from src.core.config_parser.parsers import ConfigParser
from src.core.execution.manager import ProgramOutput

app = Flask(__name__)


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


@app.route("/")
def main():
    path = parse_command_line_args(sys.argv)
    parser = ConfigParser(path)
    paths = parser.paths

    results = {}
    for path_to_exe in paths:
        test_results = []

        for test in parser.tests:
            program_output = ProgramOutput(path_to_exe, test.input, parser.timeout)
            result_stdout = program_output.result.stdout
            result_stderr = program_output.result.stderr
            result_timeout = program_output.result.timeout
            test_results.append(
                TestResult(
                    test.input,
                    test.output,
                    result_stdout,
                    result_stderr,
                    result_timeout,
                )
            )

        output_comparator = OutputComparator(test_results, path_to_exe)
        results[path_to_exe] = output_comparator.test_results
    return render_template("index.html", results=results)


if __name__ == "__main__":
    app.run()
