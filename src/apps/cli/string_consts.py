"""
Constants for strings used in the program.
"""

from dataclasses import dataclass


@dataclass
class REPORT_MESSAGES:
    """
    Constants for report messages strings.
    """

    TEST_PASSED: str = "Test passed!"
    TEST_FAILED: str = "Test failed :("
    ALL_SUCCESSFUL: str = "All tests passed :)"
    ERROR: str = "Your program contains errors :("
    TIMEOUT: str = "Your program runs for too long :("


@dataclass
class COLOR_CODES:
    """
    Constants for color codes.
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
    Constants for color codes in hex format.
    """

    HEADER: tuple = (255, 119, 255)
    NORMAL: tuple = (173, 216, 230)
    OK: tuple = (224, 255, 255)
    SUCCESS: tuple = (0, 100, 0)
    WARNING: tuple = (255, 255, 224)
    FAIL: tuple = (247, 13, 26)
    END: tuple = (0, 0, 0)
    BOLD: tuple = (255, 255, 255)
    UNDERLINE: tuple = (255, 255, 255)
