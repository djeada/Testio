"""
Implementation of the OutputComparator class.
"""

import re

from .data import ComparisonInputData, ComparisonOutputData, ComparisonResult


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

        if comparison_input_data.execution_output.stderr:
            output_data.result = ComparisonResult.EXECUTION_ERROR
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

    def _compare_unordered(self, expected: str, actual: str) -> bool:
        """
        Compares expected and actual output in an unordered manner.
        All expected lines must be present in the actual output,
        and the actual output must have the same number of lines.

        :param expected: The expected output as a string with newline-separated lines.
        :param actual: The actual output as a string with newline-separated lines.
        :return: True if all expected lines are present in actual output with same count.
        """
        expected_lines = expected.split("\n")
        actual_lines = actual.split("\n")

        # Both must have the same number of lines
        if len(expected_lines) != len(actual_lines):
            return False

        # Sort both lists and compare
        return sorted(expected_lines) == sorted(actual_lines)
