"""

"""

from dataclasses import dataclass


@dataclass
class CONFIG_SCHEMA:
    """

    """
    PROGRAM_PATH_JSON: str = "ProgramPath"
    TIMEOUT_JSON: str = "Timeout"
    TEST_JSON: str = "Test\s?\d*"
    TEST_INPUT_JSON: str = "input"
    TEST_OUTPUT_JSON: str = "output"


@dataclass
class REPORT_MESSAGES:
    """

    """
    TEST_PASSED_MSG: str = "Test passed successfully!"
    TEST_FAILED_MSG: str = "Test failed :("
    TEST_ERROR_MSG: str = "Your program contains errors :("
    TEST_TIMEOUT_MSG: str = "Your program runs for too long :("

@dataclass
class COLOR_CODES:
    """

    """
    HEADER: str = "\033[95m"
    NORMAL: str = "\033[94m"
    OK: str = "\033[96m"
    SUCCESS: str = "\033[92m"
    WARNING: str = "\033[93m"
    FAIL: str = "\033[91m"
    END: str = "\033[0m"
    BOLD: str = "\033[1m"
    UNDERLINE: str = "\033[4m"

@dataclass
class HEX_CODES:
    """

    """
    HEADER: tuple = (255, 119, 255)
    NORMAL: tuple = (173,216,230)
    OK: tuple = (224,255,255)
    SUCCESS: tuple = (50,205,50)
    WARNING: tuple = (255,255,224)
    FAIL: tuple = (247,13,26)
    END: tuple = (0, 0, 0)
    BOLD: tuple = (255, 255, 255)
    UNDERLINE: tuple = (255, 255, 255)
    

