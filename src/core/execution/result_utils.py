"""Utilities for interpreting test result data."""


def result_passed(result: dict) -> bool:
    """Return True if the result dict represents a passing (MATCH) test.

    Checks the stable ``result_name`` field first, falling back to the
    legacy ``str(Enum)`` representation for backward compatibility.
    """
    return (
        result.get("result_name") == "MATCH"
        or result.get("result") == "ComparisonResult.MATCH"
    )
