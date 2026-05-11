"""Property-based tests for OutputComparator using Hypothesis.

These tests verify algebraic invariants that must hold across all inputs,
catching edge cases (whitespace, Unicode, very long strings, empty output,
duplicate lines) that fixed examples miss.
"""

import re

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.core.execution.comparator import OutputComparator
from src.core.execution.data import (
    ComparisonInputData,
    ComparisonResult,
    ExecutionOutputData,
)

# Printable text that may contain newlines but no null bytes (safe for line-based ops)
printable_text = st.text(
    alphabet=st.characters(
        blacklist_categories=("Cs",),  # exclude surrogates
        blacklist_characters="\x00",
    ),
    max_size=200,
)

multiline_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00"),
    max_size=300,
)


def _make_input(
    expected: str,
    stdout: str,
    stderr: str = "",
    timeout: bool = False,
    unordered: bool = False,
    use_regex: bool = False,
) -> ComparisonInputData:
    return ComparisonInputData(
        input="test-input",
        expected_output=expected,
        execution_output=ExecutionOutputData(
            stdout=stdout, stderr=stderr, timeout=timeout
        ),
        unordered=unordered,
        use_regex=use_regex,
    )


comparator = OutputComparator()


# ---------------------------------------------------------------------------
# Exact-match invariants
# ---------------------------------------------------------------------------


@given(text=printable_text)
def test_exact_match_reflexive(text: str) -> None:
    """Any string exactly matches itself."""
    result = comparator.compare(_make_input(text, text))
    assert result.result == ComparisonResult.MATCH


@given(expected=printable_text, actual=printable_text)
def test_exact_mismatch_when_different(expected: str, actual: str) -> None:
    """Two different strings must not match (unless equal)."""
    assume(expected != actual)
    result = comparator.compare(_make_input(expected, actual))
    assert result.result != ComparisonResult.MATCH


@given(text=printable_text)
def test_timeout_overrides_everything(text: str) -> None:
    """TIMEOUT is returned regardless of expected/actual content."""
    result = comparator.compare(_make_input(text, text, timeout=True))
    assert result.result == ComparisonResult.TIMEOUT


@given(text=printable_text, stderr=printable_text)
def test_stderr_overrides_exact_match(text: str, stderr: str) -> None:
    """Non-empty stderr → EXECUTION_ERROR even when stdout matches expected."""
    assume(stderr.strip() != "")
    result = comparator.compare(_make_input(text, text, stderr=stderr))
    assert result.result == ComparisonResult.EXECUTION_ERROR


# ---------------------------------------------------------------------------
# Unordered (multiset) invariants
# ---------------------------------------------------------------------------


@given(lines=st.lists(st.text(alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00\n"), max_size=40), max_size=10))
def test_unordered_reflexive(lines: list) -> None:
    """A string unordered-matches itself."""
    text = "\n".join(lines)
    result = comparator.compare(_make_input(text, text, unordered=True))
    assert result.result == ComparisonResult.MATCH


@given(
    lines=st.lists(
        st.text(
            alphabet=st.characters(
                blacklist_categories=("Cs",), blacklist_characters="\x00\n"
            ),
            min_size=1,
            max_size=20,
        ),
        min_size=1,
        max_size=8,
    )
)
def test_unordered_permutation_matches(lines: list) -> None:
    """Reversing lines must still match under unordered comparison."""
    expected = "\n".join(lines)
    actual = "\n".join(reversed(lines))
    result = comparator.compare(_make_input(expected, actual, unordered=True))
    assert result.result == ComparisonResult.MATCH


@given(
    lines=st.lists(
        st.text(
            alphabet=st.characters(
                blacklist_categories=("Cs",), blacklist_characters="\x00\n"
            ),
            min_size=1,
            max_size=20,
        ),
        min_size=1,
        max_size=8,
    ),
    extra=st.text(
        alphabet=st.characters(
            blacklist_categories=("Cs",), blacklist_characters="\x00\n"
        ),
        min_size=1,
        max_size=20,
    ),
)
def test_unordered_extra_line_mismatches(lines: list, extra: str) -> None:
    """Adding an extra non-empty line to actual must break unordered match."""
    assume(extra.strip() != "")
    assume(extra not in lines)
    expected = "\n".join(lines)
    actual = "\n".join(lines + [extra])
    result = comparator.compare(_make_input(expected, actual, unordered=True))
    assert result.result != ComparisonResult.MATCH


# ---------------------------------------------------------------------------
# Regex invariants
# ---------------------------------------------------------------------------


@given(text=printable_text)
def test_regex_literal_match(text: str) -> None:
    """Escaping a string and using it as a regex pattern always matches itself."""
    pattern = re.escape(text)
    result = comparator.compare(_make_input(pattern, text, use_regex=True))
    assert result.result == ComparisonResult.MATCH


@given(pattern=printable_text)
@settings(max_examples=200)
def test_invalid_regex_does_not_raise(pattern: str) -> None:
    """An invalid regex pattern must not propagate an exception — result is MISMATCH."""
    try:
        result = comparator.compare(_make_input(pattern, "anything", use_regex=True))
        # Either MATCH or MISMATCH is acceptable; no exception is the invariant.
        assert result.result in (ComparisonResult.MATCH, ComparisonResult.MISMATCH)
    except Exception as exc:
        pytest.fail(f"Unexpected exception for pattern {pattern!r}: {exc}")


@given(text=printable_text)
def test_dot_star_matches_anything(text: str) -> None:
    """The regex '.*' (with re.DOTALL) should match any single-line string.

    Note: ``re.fullmatch`` is used by the comparator, so '.*' won't match
    strings containing newlines unless re.DOTALL is active.  We restrict
    ``text`` to lines without newlines here.
    """
    assume("\n" not in text)
    result = comparator.compare(_make_input(".*", text, use_regex=True))
    assert result.result == ComparisonResult.MATCH


# ---------------------------------------------------------------------------
# Output data propagation
# ---------------------------------------------------------------------------


@given(inp=printable_text, expected=printable_text, stdout=printable_text)
def test_output_fields_propagated(inp: str, expected: str, stdout: str) -> None:
    """compare() always propagates input, expected_output, and output fields."""
    data = ComparisonInputData(
        input=inp,
        expected_output=expected,
        execution_output=ExecutionOutputData(stdout=stdout),
    )
    out = comparator.compare(data)
    assert out.input == inp
    assert out.expected_output == expected
    assert out.output == stdout
