"""
Implementation of the OutputComparator class.
"""

import re
import signal

from .data import (
    ComparisonInputData,
    ComparisonOutputData,
    ComparisonResult,
    ExecutionOutputData,
)


class OutputComparator:
    """
    Used to compare the actual output of a program with the expected output.
    Saves the result of the comparison in a ComparisonOutputData object.
    """

    def compare(
        self, comparison_input_data: ComparisonInputData
    ) -> ComparisonOutputData:
        """
        Compares the actual output of a program with the expected output.

        :param comparison_input_data: The data to compare.
        :return: The result of the comparison.
        """

        output_data = ComparisonOutputData(
            input=comparison_input_data.input,
            expected_output=comparison_input_data.expected_output,
            output=comparison_input_data.execution_output.stdout,
            error=comparison_input_data.execution_output.stderr,
            result=ComparisonResult.MISMATCH,
        )

        if comparison_input_data.execution_output.timeout:
            output_data.result = ComparisonResult.TIMEOUT
            return output_data

        if self._is_execution_error(comparison_input_data.execution_output):
            output_data.result = ComparisonResult.EXECUTION_ERROR
            if not output_data.error:
                output_data.error = self._describe_exit(
                    comparison_input_data.execution_output.returncode
                )
            return output_data

        # Perform comparison based on mode
        if comparison_input_data.unordered:
            # Use unordered comparison - all expected lines must be present
            # regardless of order
            if self._compare_unordered(
                comparison_input_data.expected_output,
                comparison_input_data.execution_output.stdout,
            ):
                output_data.result = ComparisonResult.MATCH
        elif comparison_input_data.use_regex:
            # Use regex matching
            try:
                if re.fullmatch(
                    comparison_input_data.expected_output,
                    comparison_input_data.execution_output.stdout,
                ):
                    output_data.result = ComparisonResult.MATCH
                # If no match, result remains MISMATCH (default)
            except re.error:
                # Invalid regex pattern - result remains MISMATCH (default)
                pass
        else:
            # Use exact string matching
            if (
                comparison_input_data.expected_output
                == comparison_input_data.execution_output.stdout
            ):
                output_data.result = ComparisonResult.MATCH

        return output_data

    @staticmethod
    def _is_execution_error(execution_output: ExecutionOutputData) -> bool:
        if execution_output.output_truncated:
            return True
        if execution_output.returncode is None:
            # Exit status unknown: fall back to the legacy stderr heuristic.
            return bool(execution_output.stderr)
        # Warnings on stderr are fine; a non-zero exit (or a signal) is not.
        return execution_output.returncode != 0

    @staticmethod
    def _describe_exit(returncode: "int | None") -> str:
        if returncode is not None and returncode < 0:
            try:
                name = signal.Signals(-returncode).name
            except ValueError:
                name = f"signal {-returncode}"
            return f"Program was terminated by {name}."
        return f"Program exited with status {returncode}."

    def _compare_unordered(self, expected: str, actual: str) -> bool:
        """Compare output lines as a multiset (order-independent, duplicate-aware).

        Returns True if the actual output contains exactly the same lines as
        the expected output, regardless of order but respecting duplicates.
        """
        from collections import Counter

        expected_lines = [line for line in expected.splitlines() if line.strip()]
        actual_lines = [line for line in actual.splitlines() if line.strip()]
        return Counter(expected_lines) == Counter(actual_lines)
