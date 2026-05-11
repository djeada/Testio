from src.core.execution.comparator import OutputComparator
from src.core.execution.data import (
    ComparisonInputData,
    ComparisonOutputData,
    ComparisonResult,
    ExecutionOutputData,
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


def test_to_dict_exposes_stable_result_name():
    output = ComparisonOutputData(result=ComparisonResult.EXECUTION_ERROR)

    assert output.to_dict()["result_name"] == "EXECUTION_ERROR"


def test_compare_unordered_returns_true_for_same_lines_different_order():
    comparator = OutputComparator()

    assert comparator._compare_unordered("line1\nline2\nline3", "line3\nline1\nline2")


def test_compare_unordered_returns_true_for_matching_duplicate_lines():
    comparator = OutputComparator()

    assert comparator._compare_unordered("line1\nline1\nline2", "line2\nline1\nline1")


def test_compare_unordered_returns_false_for_different_duplicate_counts():
    comparator = OutputComparator()

    assert not comparator._compare_unordered(
        "line1\nline1\nline2", "line1\nline2\nline2"
    )
