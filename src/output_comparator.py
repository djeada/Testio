"""
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

from fpdf import FPDF, HTMLMixin

from src.string_consts import (
    COLOR_CODES, HEX_CODES, REPORT_MESSAGES
)


class PDF(FPDF, HTMLMixin):
    pass


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

        pdf = PDF(format="letter")
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        msg = f"{COLOR_CODES.HEADER}Results for {self.path.name} \n" \
              f"Passed: {len(self.successful_tests)}/{len(self.test_results)} " \
              f"Failed: {len(self.test_results) - len(self.successful_tests)}" \
              f"/{len(self.test_results)}{COLOR_CODES.END}"

        print(msg)
        pdf.multi_cell(0, 5, msg[5:-3].split("\n")[0] + "\n")
        pdf.multi_cell(0, 5, msg[5:-3].split("\n")[1] + "\n")

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

        if test.stdout is not None:
            if test.stdout == test.output:
                color = COLOR_CODES.SUCCESS
                msg = f"{color}All tests passed{COLOR_CODES.END}"
                print(msg)
                if pdf is not None:
                    pdf.set_text_color(*HEX_CODES.SUCCESS)
                    pdf.multi_cell(0, 5, msg[5:-3] + "\n")
            else:
                color = COLOR_CODES.FAIL
                msg = f"{color}Some tests failed{COLOR_CODES.END}"
                print(msg)
                if pdf is not None:
                    pdf.set_text_color(*HEX_CODES.FAIL)
                    pdf.multi_cell(0, 5, msg[5:-3] + "\n")
                if test.stderr is not None:
                    color = COLOR_CODES.FAIL
                    print(f"{color}Error: {test.stderr}{COLOR_CODES.END}")
                    if pdf is not None:
                        pdf.set_text_color(*HEX_CODES.FAIL)
                        pdf.multi_cell(0, 5, f"{color}Error: {test.stderr}{COLOR_CODES.END}\n")
        else:
            color = COLOR_CODES.WARNING
            msg = f"{color}Test timed out{COLOR_CODES.END}"
            print(msg)
            if pdf is not None:
                pdf.set_text_color(*HEX_CODES.WARNING)
                pdf.multi_cell(0, 5, msg[5:-3] + "\n")

        msg_1 = "{}{: >20} {: >20} {: >20}".format(color, "Input", "Expected output", "Actual output")
        msg_2 = "{: >20} {: >20} {: >20}{}".format(test.input, test.output, test.stdout, COLOR_CODES.END)

        print(msg_1)
        print(msg_2)

        if pdf is not None:
            pdf.write_html(f"""<table border="0" align="left" width="100%">
                                <thead>
                                    <tr>
                                        <th align="left" width="33%">Input</th>
                                        <th align="left" width="33%">Expected output</th>
                                        <th align="left" width="33%">Actual output</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>{test.input}</td>
                                        <td>{test.output}</td>
                                        <td>{test.stdout}</td>
                                    </tr>
                                </tbody>
                            </table>""")

    @staticmethod
    def display_error_msg(message):
        """
        Displays the error message.
        """
        print(f"{COLOR_CODES.FAIL}{REPORT_MESSAGES.TEST_ERROR_MSG}{COLOR_CODES.END}")
        print(message)

    @staticmethod
    def display_timeout_msg():
        """
        Displays a message when a test times out.
        """
        print("{}{}{}".format(COLOR_CODES.WARNING, REPORT_MESSAGES.TEST_TIMEOUT_MSG, COLOR_CODES.END))
