import pytest

from src.core.execution.comparator import OutputComparator
from src.core.execution.data import (
    ComparisonInputData,
    ComparisonOutputData,
    ComparisonResult,
    ExecutionOutputData,
)


def test_compare_unordered_match_same_order():
    """Test unordered matching when lines are in the same order."""
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output="line1\nline2\nline3",
        execution_output=ExecutionOutputData(
            stdout="line1\nline2\nline3", stderr="", timeout=False
        ),
        unordered=True,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.MATCH


def test_compare_unordered_match_different_order():
    """Test unordered matching when lines are in different order."""
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output="line1\nline2\nline3",
        execution_output=ExecutionOutputData(
            stdout="line3\nline1\nline2", stderr="", timeout=False
        ),
        unordered=True,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.MATCH


def test_compare_unordered_match_reversed():
    """Test unordered matching when lines are completely reversed."""
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output="apple\nbanana\ncherry",
        execution_output=ExecutionOutputData(
            stdout="cherry\nbanana\napple", stderr="", timeout=False
        ),
        unordered=True,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.MATCH


def test_compare_unordered_mismatch_missing_line():
    """Test unordered matching fails when a line is missing."""
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output="line1\nline2\nline3",
        execution_output=ExecutionOutputData(
            stdout="line1\nline2", stderr="", timeout=False
        ),
        unordered=True,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.MISMATCH


def test_compare_unordered_mismatch_extra_line():
    """Test unordered matching fails when there's an extra line."""
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output="line1\nline2",
        execution_output=ExecutionOutputData(
            stdout="line1\nline2\nline3", stderr="", timeout=False
        ),
        unordered=True,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.MISMATCH


def test_compare_unordered_mismatch_wrong_content():
    """Test unordered matching fails when content is different."""
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output="line1\nline2\nline3",
        execution_output=ExecutionOutputData(
            stdout="line1\nline2\nline4", stderr="", timeout=False
        ),
        unordered=True,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.MISMATCH


def test_compare_unordered_match_single_line():
    """Test unordered matching with a single line."""
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output="single line",
        execution_output=ExecutionOutputData(
            stdout="single line", stderr="", timeout=False
        ),
        unordered=True,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.MATCH


def test_compare_unordered_match_empty_output():
    """Test unordered matching with empty output."""
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output="",
        execution_output=ExecutionOutputData(stdout="", stderr="", timeout=False),
        unordered=True,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.MATCH


def test_compare_unordered_match_duplicate_lines():
    """Test unordered matching with duplicate lines."""
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output="line1\nline1\nline2",
        execution_output=ExecutionOutputData(
            stdout="line2\nline1\nline1", stderr="", timeout=False
        ),
        unordered=True,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.MATCH


def test_compare_unordered_mismatch_duplicate_count():
    """Test unordered matching fails when duplicate counts differ."""
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output="line1\nline1\nline2",
        execution_output=ExecutionOutputData(
            stdout="line1\nline2\nline2", stderr="", timeout=False
        ),
        unordered=True,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.MISMATCH


def test_compare_unordered_with_timeout():
    """Test that timeout takes precedence over unordered matching."""
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output="line1\nline2",
        execution_output=ExecutionOutputData(
            stdout="line2\nline1", stderr="", timeout=True
        ),
        unordered=True,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.TIMEOUT


def test_compare_unordered_with_execution_error():
    """Test that execution error takes precedence over unordered matching."""
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output="line1\nline2",
        execution_output=ExecutionOutputData(
            stdout="line2\nline1", stderr="error occurred", timeout=False
        ),
        unordered=True,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.EXECUTION_ERROR


def test_compare_exact_match_when_unordered_disabled():
    """Test that exact matching still works when unordered is disabled."""
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output="line1\nline2\nline3",
        execution_output=ExecutionOutputData(
            stdout="line3\nline1\nline2", stderr="", timeout=False
        ),
        unordered=False,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.MISMATCH


def test_compare_unordered_match_with_trailing_newline():
    """Test unordered matching handles trailing newlines gracefully."""
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output="line1\nline2\nline3",
        execution_output=ExecutionOutputData(
            stdout="line3\nline1\nline2\n", stderr="", timeout=False
        ),
        unordered=True,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.MATCH


def test_compare_unordered_match_both_with_trailing_newlines():
    """Test unordered matching when both have trailing newlines."""
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output="line1\nline2\n",
        execution_output=ExecutionOutputData(
            stdout="line2\nline1\n", stderr="", timeout=False
        ),
        unordered=True,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.MATCH


def test_compare_unordered_numeric_lines():
    """Test unordered matching with numeric lines (non-deterministic order use case)."""
    comparator = OutputComparator()

    # Simulates a program that outputs numbers in random order
    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output="1\n2\n3\n4\n5",
        execution_output=ExecutionOutputData(
            stdout="3\n5\n1\n4\n2", stderr="", timeout=False
        ),
        unordered=True,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.MATCH
