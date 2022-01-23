"""
"""

import os
import fpdf

from src.string_consts import COLOR_CODES, TEST_TIMEOUT_MSG, TEST_PASSED_MSG, TEST_FAILED_MSG, TEST_ERROR_MSG

class OutputComparator:

    def __init__(self):
        pass

    def display_test_results(self) -> None:
        """
        Displays the results of the tests.
        """

        pdf = fpdf.FPDF(format="letter")
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        msg = "{}Results for {} Passed: {}/{} Failed: {}/{}{}".format(
            COLOR_CODES.HEADER,
            os.path.basename(self.path),
            self.successful_tests,
            len(self.results),
            len(self.results) - self.successful_tests,
            len(self.results),
            COLOR_CODES.ENDC,
        )

        print(msg)
        pdf.multi_cell(0, 5, msg[5:-3] + "\n")

        if len(self.tests) > len(self.results):
            return

        for test in self.tests:
            stdout, stderr = self.results.pop(0)
            OutputComparator.display_test_result(stdout, stderr, test, pdf)

        pdf.output(
            "test_result_{}.pdf".format(
                os.path.splitext(os.path.basename(self.path))[0]
            )
        )

    @staticmethod
    def display_test_result(stdout, stderr, test, pdf=None) -> None:
        """
        Displays the result of a test.
        There are three possible results:
        - Test passed
        - Test failed
        - Test timed out
        Different colors are used for different results.
        Additionally, a pdf is created with the result of the test.
        """
        if len(stderr) > 0:
            OutputComparator.display_error_msg(stderr)
            if pdf:
                pdf.multi_cell(0, 5, stderr + "\n")
            return

        elif stdout == test.output:
            print("{}{}".format(COLOR_CODES.OKGREEN, TEST_PASSED_MSG))
            if pdf:
                pdf.multi_cell(0, 5, TEST_PASSED_MSG + "\n")

        elif stdout == "Timeout":
            print("{}{}".format(COLOR_CODES.WARNING, TEST_TIMEOUT_MSG))
            if pdf:
                pdf.multi_cell(0, 5, TEST_TIMEOUT_MSG + "\n")

        else:
            print("{}{}".format(COLOR_CODES.FAIL, TEST_FAILED_MSG))
            if pdf:
                pdf.multi_cell(0, 5, TEST_FAILED_MSG + "\n")

        msg1 = "{:<15} {:<15} {:<15}".format("Input data:", "Expected:", "Result:")
        msg2 = "{:<15} {:<15} {:<15}{}".format(
            test.input.replace("\n", " "),
            test.output.replace("\n", " "),
            stdout.replace("\n", " "),
            COLOR_CODES.ENDC,
        )

        print(msg1)
        print(msg2)

        if pdf:
            for msg in (msg1, msg2[:-3]):
                pdf.multi_cell(0, 5, msg + "\n")

    @staticmethod
    def display_error_msg(stderr):
        """
        Displays the error message.
        """
        print(f"{COLOR_CODES.FAIL}{TEST_ERROR_MSG}{COLOR_CODES.ENDC}")
        print(stderr)

    @staticmethod
    def display_timeout_msg():
        """
        Displays a message when a test times out.
        """
        print("{}{}{}".format(COLOR_CODES.WARNING, TEST_TIMEOUT_MSG, COLOR_CODES.ENDC))