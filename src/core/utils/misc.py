"""
Contains miscellaneous functions.
"""

def files_in_dir(path: str) -> list:
    """
    Creates a list of files in the given directory.

    :param path: The path to the directory.
    :return: A list of files in the given directory.
    """
    from pathlib import Path
    return [str(file) for file in Path(path).iterdir() if file.is_file()]

def strip_carriage_return(text: str) -> str:
    """
    Strips carriage return from the given text.

    :param text: The text to strip carriage return from.
    :return: The text without carriage return.
    """
    if text:
        return text.replace("\r", "")

    return text
