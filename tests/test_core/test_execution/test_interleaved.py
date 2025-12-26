"""
Tests for interleaved input/output functionality
"""
import pytest
from src.core.config_parser.data import TestData
from src.core.execution.data import ExecutionManagerInputData
from src.core.execution.manager import ExecutionManager
from src.core.execution.interactive_runner import InteractiveRunner
from src.core.execution.data import ExecutionOutputData, ComparisonResult


def test_test_data_with_interleaved_flag():
    """Test that TestData correctly stores interleaved flag"""
    test_data = TestData(
        input=["input1", "input2"],
        output=["output1", "output2"],
        timeout=10,
        interleaved=True
    )
    assert test_data.interleaved == True


def test_test_data_default_interleaved_is_false():
    """Test that TestData defaults interleaved to False"""
    test_data = TestData(
        input=["input1"],
        output=["output1"],
        timeout=10
    )
    assert test_data.interleaved == False


def test_execution_manager_input_data_with_interleaved():
    """Test that ExecutionManagerInputData stores interleaved flag"""
    data = ExecutionManagerInputData(
        command="python test.py",
        input=["input1", "input2"],
        output=["output1", "output2"],
        timeout=10,
        interleaved=True
    )
    assert data.interleaved == True


def test_interactive_runner_simple_echo():
    """Test InteractiveRunner with a simple echo command"""
    runner = InteractiveRunner()
    result = runner.run_interleaved(
        command='python -c "name=input(); print(f\'Hello {name}\')"',
        inputs=["Alice"],
        timeout=5
    )
    
    assert result.timeout == False
    assert result.stderr == ""
    assert "Hello Alice" in result.stdout


def test_interactive_runner_multiple_inputs():
    """Test InteractiveRunner with multiple inputs"""
    runner = InteractiveRunner()
    # Create a simple Python script inline that takes multiple inputs
    script = """
import sys
name = input()
print(f'Hello {name}!')
age = input()
print(f'You are {age} years old.')
"""
    result = runner.run_interleaved(
        command=f'python -c "{script}"',
        inputs=["Bob", "30"],
        timeout=5
    )
    
    assert result.timeout == False
    assert result.stderr == ""
    assert "Hello Bob!" in result.stdout
    assert "You are 30 years old." in result.stdout


def test_execution_manager_with_interleaved_flag():
    """Test that ExecutionManager uses InteractiveRunner when interleaved=True"""
    manager = ExecutionManager()
    
    # Create test data with interleaved flag
    data = ExecutionManagerInputData(
        command='python -c "name=input(); print(f\'Hello {name}\')"',
        input=["TestUser"],
        output=["Hello TestUser"],
        timeout=5,
        interleaved=True
    )
    
    result = manager.run(data)
    
    # The result should be successful (not timeout or error)
    assert result.result in [ComparisonResult.MATCH, ComparisonResult.MISMATCH]
    assert "Hello TestUser" in result.output


def test_execution_manager_backward_compatibility():
    """Test that ExecutionManager still works with interleaved=False (default)"""
    manager = ExecutionManager()
    
    # Create test data without interleaved flag (should default to False)
    data = ExecutionManagerInputData(
        command='python -c "print(\'Hello World\')"',
        input=[],
        output=["Hello World"],
        timeout=5,
        interleaved=False
    )
    
    result = manager.run(data)
    
    assert result.result == ComparisonResult.MATCH
    assert result.output == "Hello World"


def test_interactive_runner_timeout():
    """Test that InteractiveRunner properly handles timeout"""
    runner = InteractiveRunner()
    
    # Script that sleeps longer than timeout
    result = runner.run_interleaved(
        command='python -c "import time; time.sleep(10)"',
        inputs=[],
        timeout=1
    )
    
    assert result.timeout == True
