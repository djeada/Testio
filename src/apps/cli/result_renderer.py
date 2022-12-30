"""
Defines the result renderer.

The result renderer is responsible for rendering the result of a comparison between
the expected output and the actual output of a tested program.
"""
from abc import abstractmethod, ABC

from src.apps.cli.string_consts import REPORT_MESSAGES, COLOR_CODES
from src.core.execution.data import ComparisonOutputData, ComparisonResult


class ResultRendererStrategy(ABC):
    """
    Base class for all result renderer strategies.
    """

    @abstractmethod
    def render(self, comparison_output_data: ComparisonOutputData) -> str:
        """
        Renders the result of a comparison.
        :param comparison_output_data: The data to render.
        :return: The rendered result.
        """
        pass


class ResultRendererStrategyMatch(ResultRendererStrategy):
    """
    Renders the result of a comparison when the result is a match.
    """

    def render(self, comparison_output_data: ComparisonOutputData) -> str:
        """
        Renders the result of a comparison when the result is a match.

        :param comparison_output_data: The data to render.
        :return: The rendered result.
        """

        result = f"{COLOR_CODES.OK}"
        result += f"{REPORT_MESSAGES.TEST_PASSED}\n"
        result += (
            f"Input: \n {comparison_output_data.input}\n"
            if comparison_output_data.input
            else "No input given!\n"
        )
        result += (
            f"Expected output: \n {comparison_output_data.expected_output}\n"
            if comparison_output_data.expected_output
            else "No output was expected!\n"
        )
        result += (
            f"Result: \n {comparison_output_data.output}\n"
            if comparison_output_data.output
            else "The program did not produce any output!\n"
        )
        result += f"{COLOR_CODES.END}"

        return result


class ResultRendererStrategyMismatch(ResultRendererStrategy):
    """
    Renders the result of a comparison when the result is a mismatch.
    """

    def render(self, comparison_output_data: ComparisonOutputData) -> str:
        """
        Renders the result of a comparison when the result is a mismatch.

        :param comparison_output_data: The data to render.
        :return: The rendered result.
        """
        result = f"{COLOR_CODES.FAIL}"
        result += f"{REPORT_MESSAGES.TEST_FAILED}\n"
        result += (
            f"Input: \n {comparison_output_data.input}\n"
            if comparison_output_data.input
            else "No input given!\n"
        )
        result += (
            f"Expected output: \n {comparison_output_data.expected_output}\n"
            if comparison_output_data.expected_output
            else "No output was expected!\n"
        )
        result += (
            f"Result: \n {comparison_output_data.output}\n"
            if comparison_output_data.output
            else "The program did not produce any output!\n"
        )
        result += f"{COLOR_CODES.END}"

        return result


class ResultRendererStrategyExecutionError(ResultRendererStrategy):
    """
    Renders the result of a comparison when the result is an execution error.
    """

    def render(self, comparison_output_data: ComparisonOutputData) -> str:
        """
        Renders the result of a comparison when the result is an execution error.

        :param comparison_output_data: The data to render.
        :return: The rendered result.
        """
        result = f"{COLOR_CODES.FAIL}"
        result += f"{REPORT_MESSAGES.ERROR}\n"
        result += (
            f"Input: \n {comparison_output_data.input}\n"
            if comparison_output_data.input
            else "No input given!\n"
        )
        result += f"Error: \n {comparison_output_data.error}\n"
        result += f"{COLOR_CODES.END}"

        return result


class ResultRendererStrategyTimeout(ResultRendererStrategy):
    """
    Renders the result of a comparison when the result is a timeout.
    """

    def render(self, comparison_output_data: ComparisonOutputData) -> str:
        """
        Renders the result of a comparison when the result is a timeout.

        :param comparison_output_data: The data to render.
        :return: The rendered result.
        """
        result = f"{COLOR_CODES.FAIL}"
        result += f"{REPORT_MESSAGES.TIMEOUT}\n"
        result += (
            f"Input: \n {comparison_output_data.input}\n"
            if comparison_output_data.input
            else "No input given!\n"
        )
        result += f"{COLOR_CODES.END}"

        return result


class ResultRenderer:
    """
    Renders the result of a comparison using the appropriate strategy.
    """

    def render(self, comparison_output_data: ComparisonOutputData) -> None:
        """
        Chooses the appropriate strategy and renders the result of a comparison.

        :param comparison_output_data: The data to render.
        """
        result_to_renderer_strategy = {
            ComparisonResult.MATCH: ResultRendererStrategyMatch(),
            ComparisonResult.MISMATCH: ResultRendererStrategyMismatch(),
            ComparisonResult.EXECUTION_ERROR: ResultRendererStrategyExecutionError(),
            ComparisonResult.TIMEOUT: ResultRendererStrategyTimeout(),
        }

        if comparison_output_data.result not in result_to_renderer_strategy:
            raise Exception("Invalid comparison result")

        renderer = result_to_renderer_strategy[comparison_output_data.result]
        print(renderer.render(comparison_output_data))
