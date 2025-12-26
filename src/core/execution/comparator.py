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

        # Perform comparison: regex match or exact string match
        if comparison_input_data.use_regex:
            # Use regex matching
            try:
                if re.fullmatch(
                    comparison_input_data.expected_output,
                    comparison_input_data.execution_output.stdout,
                ):
                    output_data.result = ComparisonResult.MATCH
            except re.error:
                # Invalid regex pattern - treat as mismatch
                output_data.result = ComparisonResult.MISMATCH
        else:
            # Use exact string matching
            if (
                comparison_input_data.expected_output
                == comparison_input_data.execution_output.stdout
            ):
                output_data.result = ComparisonResult.MATCH

        return output_data
