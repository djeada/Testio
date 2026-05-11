"""Module-level wrapper for ExecutionManager.run().

Defining the wrapper at module level makes it picklable for ProcessPoolExecutor
and importable from any context where the execution queue submits tasks.
"""

from src.core.execution.data import ComparisonOutputData, ExecutionManagerInputData
from src.core.execution.manager import ExecutionManager


def run_single_test(data: ExecutionManagerInputData) -> ComparisonOutputData:
    """Execute a single test case and return the comparison result.

    :param data: The execution manager input data for one test.
    :return: ComparisonOutputData with the test outcome.
    """
    return ExecutionManager().run(data)
