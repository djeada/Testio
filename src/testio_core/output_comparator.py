"""
Module for comparing outputs of programs and displaying results.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

from fpdf import FPDF, HTMLMixin

from src.testio_core.string_consts import (
    COLOR_CODES, HEX_CODES, REPORT_MESSAGES
)


class PDF(FPDF, HTMLMixin):
    """
    Used to generate pdf files. Inherits from FPDF and HTMLMixin.
    HTMLMixin allows for generation of pdf files from html.
    """
    pass


@dataclass
class TestResult:
    """
    Class that represents the result of a test.
    """
    input: str
    output: str
    stdout: Optional[str] = ''
    stderr: Optional[str] = ''
    timeout: Optional[bool] = False

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
            if test.stdout and test.stdout == test.output
        ]
        self.failed_tests = [test for test in self.test_results if not (test.stdout and test.stdout == test.output)]

        self.msg = f"{COLOR_CODES.HEADER}Results for {self.path.name} \n" \
                   f"Passed: {len(self.successful_tests)}/{len(self.test_results)} " \
                   f"Failed: {len(self.test_results) - len(self.successful_tests)}" \
                   f"/{len(self.test_results)}{COLOR_CODES.END}"

    def display_test_results(self) -> None:
        """
        Displays the results of the tests.
        """

        print(self.msg)

        for i, test in enumerate(self.test_results):
            self.display_test_result(test, i+1)

    def generate_pdf_report(self) -> None:
        """
        Generates a pdf report. The report contains the results of the tests.
        """
        pdf = PDF(format="letter")
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.multi_cell(0, 5, self.msg[5:-3].split("\n")[0] + "\n")
        pdf.multi_cell(0, 5, self.msg[5:-3].split("\n")[1] + "\n\n")

        for i, test in enumerate(self.test_results):
            self.append_test_to_pdf(test, pdf, i+1)

        pdf.output(f"test_result_{self.path.stem}.pdf")

    @staticmethod
    def display_test_result(test: TestResult, i: int) -> None:
        """
        Displays the result of a test.
        There are three possible results:
        - Test passed
        - Test failed
        - Test timed out
        Different colors are used for different results.
        Additionally, a pdf is created with the result of the test.
        """

        if test.stdout:
            if test.stdout == test.output:
                color = COLOR_CODES.SUCCESS
                msg = f"{color}{i}.{REPORT_MESSAGES.TEST_PASSED}{COLOR_CODES.END}"
                print(msg)
            else:
                color = COLOR_CODES.FAIL
                msg = f"{color}{i}.{REPORT_MESSAGES.TEST_FAILED}{COLOR_CODES.END}"
                print(msg)
        elif test.stderr:
            color = COLOR_CODES.FAIL
            print(f"{color}Error: {test.stderr}{COLOR_CODES.END}")

        else:
            color = COLOR_CODES.WARNING
            msg = f"{color}{REPORT_MESSAGES.TIMEOUT}{COLOR_CODES.END}"
            print(msg)

        print("{}{: >20} {: >20} {: >20}".format(color, "Input", "Expected output", "Actual output"))

        test_inputs = test.input.split('\n')
        test_output = test.output.split('\n')
        result_stdout = test.stdout.split('\n')

        n = max((len(test_inputs), len(test_output), len(result_stdout)))

        test_inputs.extend([''] * n)
        test_output.extend([''] * n)
        result_stdout.extend([''] * n)

        for test_input, test_output, stdout in zip(test_inputs, test_output, result_stdout):
            print("{: >20} {: >20} {: >20}".format(test_input, test_output, stdout))

        print(f'{COLOR_CODES.END}', end='')

    @staticmethod
    def append_test_to_pdf(test: TestResult, pdf: PDF, i: int) -> None:
        """
        Appends a test to a pdf. The test is displayed in a table.
        """
        pdf.set_font("Arial", size=12)

        if test.stdout:
            if test.stdout == test.output:
                msg = f"{i}.{REPORT_MESSAGES.TEST_PASSED}"
                pdf.set_text_color(*HEX_CODES.SUCCESS)
                #pdf.multi_cell(0, 5, msg)
            else:
                msg = f"{i}.{REPORT_MESSAGES.TEST_FAILED}"
                pdf.set_text_color(*HEX_CODES.FAIL)
                #pdf.multi_cell(0, 5, msg)
        elif test.stderr:
            pdf.set_text_color(*HEX_CODES.FAIL)
            msg = f"Error: {test.stderr}"
            #pdf.multi_cell(0, 5, f"Error: {test.stderr}")
        else:
            msg = f"{i}.{REPORT_MESSAGES.TIMEOUT}"
            pdf.set_text_color(*HEX_CODES.WARNING)
            #pdf.multi_cell(0, 5, msg)

        pdf.write_html(f"""<p>{msg}</p><table border="0" align="left" width="100%">
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
    def display_error_msg(message: str) -> None:
        """
        Displays the error message.
        """
        print(f"{COLOR_CODES.FAIL}{REPORT_MESSAGES.ERROR}{COLOR_CODES.END}")
        print(message)

    @staticmethod
    def display_timeout_msg() -> None:
        """
        Displays a message when a test times out.
        """
        print("{}{}{}".format(COLOR_CODES.WARNING, REPORT_MESSAGES.TIMEOUT, COLOR_CODES.END))
