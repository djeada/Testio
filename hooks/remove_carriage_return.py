# get file name from command line
import sys
import pathlib


def remove_carriage_return(file_name: str) -> None:
    """
    Remove carriage return from file
    """
    # read file contents
    with open(file_name, "rb") as file:
        contents = file.read()

    # remove carriage return from bytes
    contents = contents.replace(b"\r", b"")

    # write file contents in binary mode
    with open(file_name, "wb") as file:
        file.write(contents)


if __name__ == "__main__":

    # check if user provided file name
    if len(sys.argv) != 2:
        print("Usage: python remove_carriage_return.py <dir_name>")
        exit()

    # check if file exists
    file_name = sys.argv[1]

    if not pathlib.Path(file_name).is_dir():
        print("Dir does not exist")
        exit()

    # find all files in directory and remove carriage return
    for file in pathlib.Path(file_name).glob("**/*"):
        if file.is_file():
            remove_carriage_return(file)
