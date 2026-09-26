"""
Defines the InteractiveRunner class for executing programs with batched stdin/stdout.

Despite the name, this module does not implement true line-by-line interleaving.
It joins all provided input, sends it to the program in one go, and then
collects stdout/stderr after the process finishes or times out.
"""

from .command_utils import split_command
from .data import ExecutionOutputData
from .process import run_process
from .runner import to_execution_output, with_trailing_newline


class InteractiveRunner:
    """
    Runs an external program with interleaved input/output support.
    This runner handles programs that produce output, wait for input, produce more output, etc.
    """

    def run_interleaved(
        self, command: str, inputs: list, timeout: int, cwd: str = ""
    ) -> ExecutionOutputData:
        """
        Runs a program using sequential stdin/stdout collection.

        This method does not perform true interactive, line-by-line interleaving.
        It is equivalent to joining all input lines, sending them at once, and
        collecting the resulting stdout/stderr afterward.

        :param command: The command to execute
        :param inputs: List of input strings to provide
        :param timeout: Maximum time to wait for the program
        :param cwd: Working directory for the program (empty: inherit)
        :return: ExecutionOutputData with collected stdout, stderr, and timeout status
        """
        try:
            result = run_process(
                split_command(command),
                input_text=with_trailing_newline("\n".join(inputs)),
                timeout=timeout,
                cwd=cwd or None,
            )
        except (OSError, ValueError) as exc:
            return ExecutionOutputData(
                stdout="",
                stderr=f"Error during interactive execution: {exc}",
                timeout=False,
                returncode=-1,
            )

        return to_execution_output(result)
