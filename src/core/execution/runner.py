"""
Defines the Runner class for executing an external program.
"""

import subprocess

from src.apps.server.settings import get_sandbox_cpu_secs, get_sandbox_mem_mb
from src.core.execution.sandbox import make_preexec_fn
from src.core.utils.misc import strip_carriage_return

from .command_utils import split_command
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
        preexec_fn = make_preexec_fn(get_sandbox_cpu_secs(), get_sandbox_mem_mb())
        try:
            result = subprocess.run(
                split_command(input_data.command),
                input=input_data.input,
                capture_output=True,
                text=True,
                timeout=input_data.timeout,
                preexec_fn=preexec_fn,
            )
        except subprocess.TimeoutExpired:
            return ExecutionOutputData(timeout=True)
        except OSError as exc:
            return ExecutionOutputData(stderr=str(exc), timeout=False)

        stdout = strip_carriage_return(result.stdout.rstrip("\n"))
        stderr = strip_carriage_return(result.stderr)

        return ExecutionOutputData(stdout=stdout, stderr=stderr, timeout=False)
