"""
Defines the Runner class for executing an external program.
"""

from testio.core.utils.misc import strip_carriage_return

from .command_utils import split_command
from .data import ExecutionInputData, ExecutionOutputData
from .process import ProcessResult, run_process


def to_execution_output(result: ProcessResult) -> ExecutionOutputData:
    """Normalise a raw process result into the data the comparator consumes."""
    if result.timed_out:
        return ExecutionOutputData(
            stdout=strip_carriage_return(result.stdout.rstrip("\n")),
            stderr=strip_carriage_return(result.stderr),
            timeout=True,
            returncode=result.returncode,
        )

    stderr = strip_carriage_return(result.stderr)
    if result.output_truncated:
        note = "Output limit exceeded; the program was terminated."
        stderr = f"{stderr}\n{note}" if stderr else note

    return ExecutionOutputData(
        stdout=strip_carriage_return(result.stdout.rstrip("\n")),
        stderr=stderr,
        timeout=False,
        returncode=result.returncode,
        output_truncated=result.output_truncated,
    )


def with_trailing_newline(text: str) -> str:
    """Terminate stdin like a terminal would, so line readers see every line."""
    if text and not text.endswith("\n"):
        return text + "\n"
    return text


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
        try:
            result = run_process(
                split_command(input_data.command),
                input_text=with_trailing_newline(input_data.input),
                timeout=input_data.timeout,
                cwd=input_data.cwd or None,
            )
        except (OSError, ValueError) as exc:
            return ExecutionOutputData(stderr=str(exc), timeout=False, returncode=-1)

        return to_execution_output(result)
