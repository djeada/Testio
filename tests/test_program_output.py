import unittest
import sys
from io import StringIO
from src.testio import ProgramOutput


def check_output(function, expected_output):
    """
    """
    saved_stdout = sys.stdout
    try:
        out = StringIO()
        sys.stdout = out
        function()
        output = out.getvalue().strip()
        assert output == expected_output
    finally:
        sys.stdout = saved_stdout


class TestProgramOutput(unittest.TestCase):
    def test_display_test_result(self):
        pass

    def test_display_error_msg(self):
        pass

    def test_display_timeout_msg(self):
        pass


if __name__ == "__main__":
    unittest.main()
