import pytest
from typing import Dict, Union

from src.core.execution.comparator import OutputComparator
from src.core.execution.data import (
    ComparisonInputData,
    ExecutionOutputData,
    ComparisonOutputData,
    ComparisonResult,
)


def test_compare_timeout():
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output="expected_output",
        execution_output=ExecutionOutputData(stdout="", stderr="", timeout=True),
    )

    expected_output = ComparisonOutputData(
        input="input",
        expected_output="expected_output",
        output="",
        error="",
        result=ComparisonResult.TIMEOUT,
    )

    result = comparator.compare(comparison_input_data)
    assert result.to_dict() == expected_output.to_dict()


def test_compare_execution_error():
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output="expected_output",
        execution_output=ExecutionOutputData(stdout="", stderr="error", timeout=False),
    )

    expected_output = ComparisonOutputData(
        input="input",
        expected_output="expected_output",
        output="",
        error="error",
        result=ComparisonResult.EXECUTION_ERROR,
    )

    result = comparator.compare(comparison_input_data)
    assert result.to_dict() == expected_output.to_dict()


def test_compare_mismatch():
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output="expected_output",
        execution_output=ExecutionOutputData(
            stdout="actual_output", stderr="", timeout=False
        ),
    )

    expected_output = ComparisonOutputData(
        input="input",
        expected_output="expected_output",
        output="actual_output",
        error="",
        result=ComparisonResult.MISMATCH,
    )

    result = comparator.compare(comparison_input_data)
    assert result.to_dict() == expected_output.to_dict()


def test_compare_match():
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output="expected_output",
        execution_output=ExecutionOutputData(
            stdout="expected_output", stderr="", timeout=False
        ),
    )

    expected_output = ComparisonOutputData(
        input="input",
        expected_output="expected_output",
        output="expected_output",
        error="",
        result=ComparisonResult.MATCH,
    )

    result = comparator.compare(comparison_input_data)
    assert result.to_dict() == expected_output.to_dict()
