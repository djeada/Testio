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
    ExecutionInputData,
    ExecutionManagerInputData,
)
from .runner import Runner
from .interactive_runner import InteractiveRunner


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

        # convert input from list to string separated by newlines
        data_input = "\n".join(data.input)
        data_output = "\n".join(data.output)

        if data.interleaved:
            # Use InteractiveRunner for interleaved I/O
            interactive_runner = InteractiveRunner()
            execution_output = interactive_runner.run_interleaved(
                command=data.command,
                inputs=data.input,
                timeout=data.timeout,
            )
        else:
            # Use standard Runner for sequential I/O
            runner_input_data = ExecutionInputData(
                command=data.command,
                input=data_input,
                timeout=data.timeout,
            )

            runner = Runner()
            execution_output = runner.run(runner_input_data)

        comparison_input_data = ComparisonInputData(
            input=data_input,
            expected_output=data_output,
            execution_output=execution_output,
        )

        comparator = OutputComparator()
        comparison_output = comparator.compare(comparison_input_data)

        return comparison_output
