"""
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

import fpdf

from src.string_consts import (
    COLOR_CODES,
    TEST_TIMEOUT_MSG,
    TEST_PASSED_MSG,
    TEST_FAILED_MSG,
    TEST_ERROR_MSG,
)


@dataclass
class TestResult:
    """
    Class that represents the result of a test.
    """

    input: str
    output: str
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    timeout: Optional[bool] = None

    def __post_init__(self) -> None:

        if len([x for x in [self.stdout, self.stderr, self.timeout] if x]) != 1:
            raise Exception(
                "You have to provide exactly one of the following parameters: stdout, stderr, timeout"
            )


class OutputComparator:
    """
    The purpose of this class is to display the results of the tests.
    The results are displayed on the standard output.
    A pdf report is also created and saved in the same directory as the application.     
    """
    def __init__(self, test_results: List[TestResult], path_to_exe: Path) -> None:
        self.test_results = test_results
        self.path = path_to_exe
        self.successful_tests = [
            test
            for test in self.test_results
            if test.stdout is not None and test.stdout == test.output
        ]
        self.failed_tests = [test for test in self.test_results if test.stdout is None]

    def display_test_results(self) -> None:
        """
        Displays the results of the tests.
        """

        pdf = fpdf.FPDF(format="letter")
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        msg = f"{COLOR_CODES.HEADER}Results for {self.path.name} " \
              f"Passed: { len(self.successful_tests)}/{len(self.test_results)} " \
              f"Failed: {len(self.test_results) - len(self.successful_tests)}" \
              f"/{len(self.test_results)}{COLOR_CODES.ENDC}"

        print(msg)
        pdf.multi_cell(0, 5, msg[5:-3] + "\n")

        for test in self.test_results:
            self.display_test_result(test, pdf)

        pdf.output(f"test_result_{self.path.stem}.pdf")

    @staticmethod
    def display_test_result(test, pdf=None) -> None:
        """
        Displays the result of a test.
        There are three possible results:
        - Test passed
        - Test failed
        - Test timed out
        Different colors are used for different results.
        Additionally, a pdf is created with the result of the test.
        """
        if len(test.stderr) > 0:
            OutputComparator.display_error_msg(test.stderr)
            if pdf:
                pdf.multi_cell(0, 5, test.stderr + "\n")
            return

        elif test.stdout == test.output:
            print("{}{}".format(COLOR_CODES.OKGREEN, TEST_PASSED_MSG))
            if pdf:
                pdf.multi_cell(0, 5, TEST_PASSED_MSG + "\n")

        elif test.stdout == "Timeout":
            print("{}{}".format(COLOR_CODES.WARNING, TEST_TIMEOUT_MSG))
            if pdf:
                pdf.multi_cell(0, 5, TEST_TIMEOUT_MSG + "\n")

        else:
            print("{}{}".format(COLOR_CODES.FAIL, TEST_FAILED_MSG))
            if pdf:
                pdf.multi_cell(0, 5, TEST_FAILED_MSG + "\n")

        msg1 = "{:<20} {:<20} {:<20}".format("Input data:", "Expected:", "Result:")
        msg2 = "{:<20} {:<20} {:<20}{}".format(
            test.input.replace("\n", " "),
            test.output.replace("\n", " "),
            test.stdout.replace("\n", " "),
            COLOR_CODES.ENDC,
        )

        print(msg1)
        print(msg2)

        if pdf:
            for msg in (msg1, msg2[:-3]):
                pdf.multi_cell(0, 5, msg + "\n")

    @staticmethod
    def display_error_msg(message):
        """
        Displays the error message.
        """
        print(f"{COLOR_CODES.FAIL}{TEST_ERROR_MSG}{COLOR_CODES.ENDC}")
        print(message)

    @staticmethod
    def display_timeout_msg():
        """
        Displays a message when a test times out.
        """
        print("{}{}{}".format(COLOR_CODES.WARNING, TEST_TIMEOUT_MSG, COLOR_CODES.ENDC))
