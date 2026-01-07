"""
Handles compilation of programs before execution.
Supports compiled languages like C, C++, Java, Go, Rust, etc.
"""

import subprocess
from pathlib import Path
from typing import Optional


class CompilationError(Exception):
    """Raised when compilation fails."""
    def __init__(self, stderr: str, returncode: int):
        self.stderr = stderr
        self.returncode = returncode
        super().__init__(f"Compilation failed with exit code {returncode}:\n{stderr}")


class Compiler:
    """
    Handles compilation of programs before they can be executed.
    """

    def compile(
        self,
        compile_command: str,
        source_path: str,
        timeout: int = 30
    ) -> Optional[str]:
        """
        Compiles the source file using the provided compilation command.
        
        :param compile_command: The compilation command template (e.g., "gcc {source} -o {output}")
        :param source_path: Path to the source file
        :param timeout: Compilation timeout in seconds
        :return: Path to the compiled executable or None if compilation failed
        :raises CompilationError: If compilation fails
        """
        if not compile_command:
            return None
            
        source_path_obj = Path(source_path).resolve()
        output_path = source_path_obj.parent / source_path_obj.stem
        
        # Use just the filename for source and output when running in the directory
        source_filename = source_path_obj.name
        output_filename = source_path_obj.stem
        
        # Replace placeholders in the compile command
        command = compile_command.replace("{source}", source_filename)
        command = command.replace("{output}", output_filename)
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(source_path_obj.parent)
            )
            
            if result.returncode != 0:
                raise CompilationError(result.stderr, result.returncode)
                
            return str(output_path)
            
        except subprocess.TimeoutExpired:
            raise CompilationError(
                f"Compilation timed out after {timeout} seconds",
                -1
            )
