import os
import errno


def get_leading_path(path: str) -> str:
    """
    Returns the leading path of the given path.
    """
    head, _ = os.path.split(path)
    return head


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


def file_exists(path) -> bool:
    """
    Checks if the given path exists.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path)

    return True


def strip_carriage_return(text: str) -> str:
    """
    Strips the carriage return from the given text.
    """
    if text and text[-1] == '\r':
        return text[:-1]

    return text
