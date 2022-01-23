"""
This module contains the ProgramOutput class.
"""

import subprocess
import multiprocessing
from dataclasses import dataclass
from typing import Optional

from src.misc import strip_carriage_return


@dataclass
class ExecutionResult:
    """
    Class that represents the result of the execution of a program.
    """

    stdout: Optional[str] = None
    stderr: Optional[str] = None
    timeout: bool = False


class ProgramOutput:
    """
	Displays the result of a test.
	"""

    def __init__(self, path_to_exe, input_data, timeout):
        self.path = path_to_exe
        self.input_data = input_data
        self.timeout = timeout
        self.result: ExecutionResult = ExecutionResult()
        self.run()

    def run(self) -> None:
        """
        Try to execute the program. If the program times out,
        print the timeout variable is set to True.
        """
        queue = multiprocessing.Queue()
        queue.put(self.result)
        p = multiprocessing.Process(target=self.execute_program, args=(queue,))
        p.start()
        p.join(self.timeout)
        while p.is_alive():
            p.terminate()
            if not p.is_alive():
                self.result = ExecutionResult(timeout=True)
                break
        self.result = queue.get()

    def execute_program(self, queue) -> None:
        """
        Executes the program specified with the path to the executable.
        Saves the output to the stdout and stderr variables.
        If the program times out, the timeout variable is set to True.
        """
        pipe = subprocess.Popen(
            "C:\\Users\\Adam\\Documents\\Programowanie\\Testio\\venv\\Scripts\\python.exe {}".format(
                self.path
            ),
            shell=True,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            communication_result = pipe.communicate(
                input=self.input_data.encode(), timeout=self.timeout
            )

        except subprocess.TimeoutExpired:
            queue.get() and queue.put(ExecutionResult(timeout=True))
            return

        stdout = communication_result[0].decode("utf-8")[:-1]
        stderr = communication_result[1].decode("utf-8")

        stdout = strip_carriage_return(stdout)
        stderr = strip_carriage_return(stderr)

        queue.get() and queue.put(ExecutionResult(stdout, stderr))
