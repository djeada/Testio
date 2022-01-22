"""
This module contains the ProgramOutput class.
"""

import subprocess
import multiprocessing
import os
import fpdf

from src.misc import strip_carriage_return
from src.string_consts import COLOR_CODES, TEST_TIMEOUT_MSG, TEST_PASSED_MSG, TEST_FAILED_MSG, TEST_ERROR_MSG


class ProgramOutput:
    """
	Displays the result of a test.
	"""

    def __init__(self, path, timeout, tests, leading_path=None):
        self.path = os.path.join(leading_path, path) if leading_path else path
        self.tests = tests
        self.timeout = timeout
        self.results = []
        self.successful_tests = 0
        self.run()

    def run(self) -> None:
        """
        Runs all tests.
        """

        for test in self.tests:
            p = multiprocessing.Process(target=self.run_test(test))
            p.start()
            p.join(self.timeout)
            while p.is_alive():
                p.terminate()
                if not p.is_alive():
                    ProgramOutput.display_timeout_msg()
        self.display_test_results()

    def run_test(self, test) -> None:
        """
        Runs a test and returns the stdout and stderr.
        """
        pipe = subprocess.Popen(
            "C:\\Users\\Adam\\Documents\\Programowanie\\Testio\\venv\\Scripts\\python.exe {}".format(self.path),
            shell=True,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            communication_result = pipe.communicate(
                input=test.input.encode(), timeout=self.timeout
            )

        except subprocess.TimeoutExpired:
            self.results.append(("Timeout", ""))
            return

        assert len(communication_result) == 2
        stdout = communication_result[0].decode("utf-8")[:-1]
        stderr = communication_result[1].decode("utf-8")

        stdout = strip_carriage_return(stdout)
        stderr = strip_carriage_return(stderr)

        if stdout == test.output and not stderr:
            self.successful_tests += 1

        self.results.append((stdout, stderr))

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
            ProgramOutput.display_test_result(stdout, stderr, test, pdf)

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
            ProgramOutput.display_error_msg(stderr)
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
