"""
Various functions used all over the code.
"""
import os


def files_in_dir(path: str) -> list:
    """
    Creates a list of files in the given directory.
    """
    result = []
    for _file in os.listdir(path):
        if os.path.isfile(os.path.join(path, _file)) and not os.path.isdir(
                os.path.join(path, _file)
        ):
            result.append(_file)

    return result


def strip_carriage_return(text: str) -> str:
    """
    Strips the carriage return from the given text.
    """
    if text:
        return text.replace('\r','')

    return text
