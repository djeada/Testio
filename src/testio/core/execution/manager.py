"""
Access point for the outside world to the execution module.
ExecutionManager is responsible for creating and using appropriate
objects in order to run the specified program and compare its output
with the expected output.
"""

from .comparator import OutputComparator
from .data import (
    ComparisonInputData,
    ComparisonOutputData,
    ComparisonResult,
    ExecutionInputData,
    ExecutionManagerInputData,
    as_lines,
)
from .interactive_runner import InteractiveRunner
from .runner import Runner


class ExecutionManager:
    """
    Runs the specified program and compares its output with the expected output.
    """

    def run(self, data: ExecutionManagerInputData) -> ComparisonOutputData:
        """
        Uses the data provided to run the specified program and compare its output
        with the expected output.

        :param data: The data to use.
        :return: The result of the comparison.
        """
        inputs = as_lines(data.input)
        data_output = "\n".join(as_lines(data.output))
        if not data.use_regex:
            # Actual stdout has its trailing newlines stripped; mirror that so a
            # trailing newline in the expected output does not cause a mismatch.
            data_output = data_output.rstrip("\n")
        display_input = "\n".join(inputs)

        if data.compile_error:
            return ComparisonOutputData(
                input=display_input,
                expected_output=data_output,
                error=data.compile_error,
                result=ComparisonResult.EXECUTION_ERROR,
            )

        if data.interleaved:
            interactive_runner = InteractiveRunner()
            execution_output = interactive_runner.run_interleaved(
                command=data.command,
                inputs=inputs,
                timeout=data.timeout,
                cwd=data.cwd,
            )
        else:
            runner_input_data = ExecutionInputData(
                command=data.command,
                input=display_input,
                timeout=data.timeout,
                cwd=data.cwd,
            )
            runner = Runner()
            execution_output = runner.run(runner_input_data)

        comparison_input_data = ComparisonInputData(
            input=display_input,
            expected_output=data_output,
            execution_output=execution_output,
            use_regex=data.use_regex,
            unordered=data.unordered,
        )

        comparator = OutputComparator()
        return comparator.compare(comparison_input_data)
