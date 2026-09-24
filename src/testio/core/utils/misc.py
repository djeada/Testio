"""
Contains miscellaneous functions.
"""

import platform


def strip_carriage_return(text: str) -> str:
    """
    Strips carriage return from the given text.

    :param text: The text to strip carriage return from.
    :return: The text without carriage return.
    """
    if text:
        return text.replace("\r", "")

    return text


def ensure_correct_newlines(text: str) -> str:
    """
    Ensures that the text has correct newlines.

    :param text: The text to ensure correct newlines.
    :return: The text with correct newlines.
    """

    if platform.system() != "Windows":
        return text.replace("\r\n", "\n")

    return text
