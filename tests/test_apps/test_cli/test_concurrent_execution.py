"""
Tests for concurrent execution of multiple files in the CLI.
"""
import tempfile
import json
from pathlib import Path
from src.apps.cli.main import process_file
from src.core.execution.data import ExecutionManagerInputData, ComparisonResult


def test_process_file_single():
    """Test that process_file works correctly for a single file."""
    # Create a temporary Python script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('print("Hello World")')
        temp_file = f.name
    
    try:
        # Create test data
        test_data = [
            ExecutionManagerInputData(
                command=f'python3 "{temp_file}"',
                input=[""],
                output=["Hello World"],
                timeout=5,
                use_regex=False,
                interleaved=False
            )
        ]
        
        # Process the file
        path, results, total_test, passed_test, ratio = process_file((temp_file, test_data))
        
        # Verify results
        assert path == temp_file
        assert total_test == 1
        assert passed_test == 1
        assert ratio == 100.0
        assert len(results) == 1
        assert results[0].result == ComparisonResult.MATCH
    finally:
        # Clean up
        Path(temp_file).unlink(missing_ok=True)


def test_process_file_multiple_tests():
    """Test that process_file works correctly with multiple tests for a single file."""
    # Create a temporary Python script that echoes input
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('x = input()\nprint(int(x) * 2)')
        temp_file = f.name
    
    try:
        # Create test data with multiple tests
        test_data = [
            ExecutionManagerInputData(
                command=f'python3 "{temp_file}"',
                input=["5"],
                output=["10"],
                timeout=5,
                use_regex=False,
                interleaved=False
            ),
            ExecutionManagerInputData(
                command=f'python3 "{temp_file}"',
                input=["3"],
                output=["6"],
                timeout=5,
                use_regex=False,
                interleaved=False
            )
        ]
        
        # Process the file
        path, results, total_test, passed_test, ratio = process_file((temp_file, test_data))
        
        # Verify results
        assert path == temp_file
        assert total_test == 2
        assert passed_test == 2
        assert ratio == 100.0
        assert len(results) == 2
        assert all(r.result == ComparisonResult.MATCH for r in results)
    finally:
        # Clean up
        Path(temp_file).unlink(missing_ok=True)


def test_concurrent_execution_multiple_files():
    """Test that multiple files can be processed concurrently."""
    from concurrent.futures import ProcessPoolExecutor
    
    # Create multiple temporary Python scripts
    temp_files = []
    test_data_list = []
    
    for i in range(3):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(f'print("{i * 10}")')
            temp_file = f.name
            temp_files.append(temp_file)
            
            test_data = [
                ExecutionManagerInputData(
                    command=f'python3 "{temp_file}"',
                    input=[""],
                    output=[f"{i * 10}"],
                    timeout=5,
                    use_regex=False,
                    interleaved=False
                )
            ]
            test_data_list.append((temp_file, test_data))
    
    try:
        # Process files concurrently
        with ProcessPoolExecutor() as executor:
            results = list(executor.map(process_file, test_data_list))
        
        # Verify results
        assert len(results) == 3
        for i, (path, file_results, total_test, passed_test, ratio) in enumerate(results):
            assert path == temp_files[i]
            assert total_test == 1
            assert passed_test == 1
            assert ratio == 100.0
            assert len(file_results) == 1
            assert file_results[0].result == ComparisonResult.MATCH
    finally:
        # Clean up
        for temp_file in temp_files:
            Path(temp_file).unlink(missing_ok=True)
