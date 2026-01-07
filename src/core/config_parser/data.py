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
    use_regex: bool = False
    interleaved: bool = False
    unordered: bool = False


@dataclass
class TestSuiteConfig:
    """
    Complete test suite configuration.
    Consists of a multiple test cases.
    
    For backward compatibility:
    - If only 'command' is provided, it's used as the run command (legacy behavior)
    - If 'run_command' is provided, it takes precedence over 'command'
    - If 'compile_command' is provided, compilation is performed before running tests
    """

    command: str
    path: str
    tests: List[TestData]
    compile_command: str = ""
    run_command: str = ""
