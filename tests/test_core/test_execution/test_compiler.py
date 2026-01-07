"""
Tests for the Compiler class
"""
import tempfile
import pytest
from pathlib import Path

from src.core.execution.compiler import Compiler, CompilationError


def test_compile_simple_c_program():
    """Test compiling a simple C program"""
    # Create a temporary C file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
        f.write("""
#include <stdio.h>
int main() {
    printf("Test\\n");
    return 0;
}
""")
        temp_c_file = f.name
    
    try:
        compiler = Compiler()
        output_path = compiler.compile(
            "gcc {source} -o {output}",
            temp_c_file
        )
        
        # Check that output file was created
        assert output_path is not None
        assert Path(output_path).exists()
        
        # Clean up compiled file
        Path(output_path).unlink()
    finally:
        Path(temp_c_file).unlink()


def test_compile_with_invalid_source():
    """Test that compilation fails with invalid C code"""
    # Create a temporary C file with invalid code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
        f.write("invalid c code here")
        temp_c_file = f.name
    
    try:
        compiler = Compiler()
        with pytest.raises(CompilationError) as exc_info:
            compiler.compile(
                "gcc {source} -o {output}",
                temp_c_file
            )
        
        assert "Compilation failed" in str(exc_info.value)
    finally:
        Path(temp_c_file).unlink()


def test_compile_with_empty_command():
    """Test that empty compile command returns None"""
    compiler = Compiler()
    result = compiler.compile("", "/some/path.c")
    assert result is None


def test_compile_with_custom_placeholders():
    """Test that {source} and {output} placeholders are replaced correctly"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
        f.write("""
#include <stdio.h>
int main() {
    return 0;
}
""")
        temp_c_file = f.name
    
    try:
        compiler = Compiler()
        output_path = compiler.compile(
            "gcc {source} -o {output}",
            temp_c_file
        )
        
        # Verify the output path
        assert output_path is not None
        source_path = Path(temp_c_file)
        expected_output = str(source_path.parent / source_path.stem)
        assert output_path == expected_output
        
        # Clean up
        if Path(output_path).exists():
            Path(output_path).unlink()
    finally:
        Path(temp_c_file).unlink()


def test_compilation_error_contains_stderr():
    """Test that CompilationError contains the stderr output"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
        f.write("this is not valid C code at all!")
        temp_c_file = f.name
    
    try:
        compiler = Compiler()
        with pytest.raises(CompilationError) as exc_info:
            compiler.compile(
                "gcc {source} -o {output}",
                temp_c_file
            )
        
        # The error should contain stderr information
        assert exc_info.value.stderr is not None
        assert exc_info.value.returncode != 0
    finally:
        Path(temp_c_file).unlink()


def test_compile_timeout():
    """Test that compilation respects timeout parameter"""
    # Create a simple C file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
        f.write("""
#include <stdio.h>
int main() {
    return 0;
}
""")
        temp_c_file = f.name
    
    try:
        compiler = Compiler()
        # Use a very short timeout that should still work for a simple program
        output_path = compiler.compile(
            "gcc {source} -o {output}",
            temp_c_file,
            timeout=5
        )
        
        assert output_path is not None
        
        # Clean up
        if Path(output_path).exists():
            Path(output_path).unlink()
    finally:
        Path(temp_c_file).unlink()
