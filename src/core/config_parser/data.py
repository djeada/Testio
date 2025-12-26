"""
Defines Python representations of the JSON configuration files.
"""

from dataclasses import dataclass
from typing import List, Union


@dataclass
class TestData:
    """
    Represents a single test case.
    """

    input: Union[str, List[str]]
    output: Union[str, List[str]]
    timeout: int
    interleaved: bool = False


@dataclass
class TestSuiteConfig:
    """
    Complete test suite configuration.
    Consists of a multiple test cases.
    """

    command: str
    path: str
    tests: List[TestData]
