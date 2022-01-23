"""

"""

# convert to dataclass

PROGRAM_PATH_JSON: str = "ProgramPath"
TIMEOUT_JSON: str = "Timeout"
TEST_JSON: str = "Test\s?\d*"
TEST_INPUT_JSON: str = "input"
TEST_OUTPUT_JSON: str = "output"
TEST_PASSED_MSG: str = "Test passed successfully!"
TEST_FAILED_MSG: str = "Test failed :("
TEST_ERROR_MSG: str = "Your program contains errors :("
TEST_TIMEOUT_MSG: str = "Your program runs for too long :("


class COLOR_CODES:
    """

    """
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
