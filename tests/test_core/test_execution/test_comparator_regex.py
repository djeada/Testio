import pytest

from src.core.execution.comparator import OutputComparator
from src.core.execution.data import (
    ComparisonInputData,
    ComparisonOutputData,
    ComparisonResult,
    ExecutionOutputData,
)


def test_compare_regex_match_simple_pattern():
    """Test regex matching with a simple pattern."""
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output=r"\d+",
        execution_output=ExecutionOutputData(stdout="123", stderr="", timeout=False),
        use_regex=True,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.MATCH


def test_compare_regex_match_timestamp_log():
    """Test regex matching with timestamp pattern (main use case)."""
    comparator = OutputComparator()

    # Pattern that matches log with timestamp: [YYYY-MM-DD HH:MM:SS] message
    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output=r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] User logged in",
        execution_output=ExecutionOutputData(
            stdout="[2023-12-26 15:30:45] User logged in", stderr="", timeout=False
        ),
        use_regex=True,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.MATCH


def test_compare_regex_mismatch():
    """Test regex matching when output doesn't match pattern."""
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output=r"\d+",
        execution_output=ExecutionOutputData(stdout="abc", stderr="", timeout=False),
        use_regex=True,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.MISMATCH


def test_compare_regex_multiline():
    """Test regex matching with multiline output."""
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output=r"Line 1\nLine 2\nLine 3",
        execution_output=ExecutionOutputData(
            stdout="Line 1\nLine 2\nLine 3", stderr="", timeout=False
        ),
        use_regex=True,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.MATCH


def test_compare_regex_wildcard():
    """Test regex matching with wildcard patterns."""
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output=r"Hello, .*!",
        execution_output=ExecutionOutputData(
            stdout="Hello, World!", stderr="", timeout=False
        ),
        use_regex=True,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.MATCH


def test_compare_regex_invalid_pattern():
    """Test behavior with invalid regex pattern."""
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output=r"[invalid(regex",
        execution_output=ExecutionOutputData(stdout="output", stderr="", timeout=False),
        use_regex=True,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.MISMATCH


def test_compare_exact_match_when_regex_disabled():
    """Test that exact matching still works when regex is disabled."""
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output="expected_output",
        execution_output=ExecutionOutputData(
            stdout="expected_output", stderr="", timeout=False
        ),
        use_regex=False,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.MATCH


def test_compare_exact_mismatch_when_regex_disabled():
    """Test that exact matching detects mismatch when regex is disabled."""
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output=r"\d+",
        execution_output=ExecutionOutputData(stdout="123", stderr="", timeout=False),
        use_regex=False,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.MISMATCH


def test_compare_regex_with_timeout():
    """Test that timeout takes precedence over regex matching."""
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output=r"\d+",
        execution_output=ExecutionOutputData(stdout="123", stderr="", timeout=True),
        use_regex=True,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.TIMEOUT


def test_compare_regex_with_execution_error():
    """Test that execution error takes precedence over regex matching."""
    comparator = OutputComparator()

    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output=r"\d+",
        execution_output=ExecutionOutputData(
            stdout="123", stderr="error occurred", timeout=False
        ),
        use_regex=True,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.EXECUTION_ERROR


def test_compare_regex_complex_log_pattern():
    """Test regex matching with complex log pattern including dynamic data."""
    comparator = OutputComparator()

    # Pattern for log with timestamp, level, and message
    comparison_input_data = ComparisonInputData(
        input="input",
        expected_output=r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - INFO - Processing request ID: [a-f0-9-]+",
        execution_output=ExecutionOutputData(
            stdout="2023-12-26 15:30:45,123 - INFO - Processing request ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            stderr="",
            timeout=False,
        ),
        use_regex=True,
    )

    result = comparator.compare(comparison_input_data)
    assert result.result == ComparisonResult.MATCH
