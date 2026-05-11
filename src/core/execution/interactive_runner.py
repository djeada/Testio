"""
Defines the InteractiveRunner class for executing programs with batched stdin/stdout.

Despite the name, this module does not implement true line-by-line interleaving.
It joins all provided input, sends it in a single communicate() call, and then
collects stdout/stderr after the process finishes or times out.
"""

import subprocess

from src.apps.server.settings import get_sandbox_cpu_secs, get_sandbox_mem_mb
from src.core.execution.sandbox import make_preexec_fn
from src.core.utils.misc import strip_carriage_return

from .command_utils import split_command
from .data import ExecutionOutputData


class InteractiveRunner:
    """
    Runs an external program with interleaved input/output support.
    This runner handles programs that produce output, wait for input, produce more output, etc.
    """

    def run_interleaved(
        self, command: str, inputs: list, timeout: int
    ) -> ExecutionOutputData:
        """
        Runs a program using sequential stdin/stdout collection.

        This method does not perform true interactive, line-by-line interleaving.
        It is equivalent to joining all input lines, sending them once via
        communicate(), and collecting the resulting stdout/stderr afterward.

        :param command: The command to execute
        :param inputs: List of input strings to provide
        :param timeout: Maximum time to wait for the program
        :return: ExecutionOutputData with collected stdout, stderr, and timeout status
        """
        try:
            # Join inputs with newlines - we still provide all inputs at once
            # but the program will consume them one by one when it calls input()
            input_str = "\n".join(inputs)

            preexec_fn = make_preexec_fn(get_sandbox_cpu_secs(), get_sandbox_mem_mb())
            process = subprocess.Popen(
                split_command(command),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=preexec_fn,
            )

            try:
                # Provide all input at once and get output
                stdout, stderr = process.communicate(input=input_str, timeout=timeout)

                stdout = stdout.rstrip("\n")

                stdout = strip_carriage_return(stdout)
                stderr = strip_carriage_return(stderr)

                return ExecutionOutputData(stdout=stdout, stderr=stderr, timeout=False)

            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                return ExecutionOutputData(timeout=True)

        except OSError as exc:
            return ExecutionOutputData(
                stdout="",
                stderr=f"Error during interactive execution: {exc}",
                timeout=False,
            )
