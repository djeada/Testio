"""
Defines the Runner class for executing an external program.
"""

import multiprocessing
import subprocess

from src.core.utils.misc import strip_carriage_return

from .data import ExecutionInputData, ExecutionOutputData


class Runner:
    """
    Runs an external program and returns the output, as well
    as any errors that may have occurred during the execution.
    """

    def run(self, input_data: ExecutionInputData) -> ExecutionOutputData:
        """
        Tries to run the program specified with the path to the executable.
        If the program times out, the timeout variable is set to True.

        :param input_data: The data to use.
        :return: The output of the program.
        """
        result = ExecutionOutputData()
        queue = multiprocessing.Queue()
        queue.put(result)
        p = multiprocessing.Process(
            target=self.execute_program,
            args=(
                input_data,
                queue,
            ),
        )
        p.start()
        p.join(input_data.timeout)
        while p.is_alive():
            p.terminate()
            if not p.is_alive():
                break
        result = queue.get()
        return (
            result
            if len([x for x in [result.stdout, result.stderr, result.timeout] if x])
            != 0
            else ExecutionOutputData(timeout=True)
        )

    def execute_program(self, input_data: ExecutionInputData, queue) -> None:
        """
        Uses subprocess to execute the program and pipe the output to the queue.

        :param input_data: The data to use.
        :param queue: The queue to use.
        :return: None
        """
        pipe = subprocess.Popen(
            input_data.command,
            shell=True,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            communication_result = pipe.communicate(
                input=input_data.input.encode(), timeout=input_data.timeout
            )

        except subprocess.TimeoutExpired:
            queue.get() and queue.put(ExecutionOutputData(timeout=True))
            return

        stdout = communication_result[0].decode("utf-8")[:-1]
        stderr = communication_result[1].decode("utf-8")

        stdout = strip_carriage_return(stdout)
        stderr = strip_carriage_return(stderr)

        queue.get() and queue.put(
            ExecutionOutputData(stdout=stdout, stderr=stderr, timeout=False)
        )
