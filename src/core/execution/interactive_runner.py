"""
Defines the InteractiveRunner class for executing programs with interleaved input/output.
"""

import subprocess
import time

from src.core.utils.misc import strip_carriage_return

from .data import ExecutionOutputData


class InteractiveRunner:
    """
    Runs an external program with interleaved input/output support.
    This runner handles programs that produce output, wait for input, produce more output, etc.
    """

    def run_interleaved(
        self, command: str, inputs: list, timeout: int
    ) -> ExecutionOutputData:
        """
        Runs a program with interleaved input/output.
        Unlike the standard runner, this uses line-buffered I/O and can handle
        programs that alternate between prompting and waiting for input.
        
        :param command: The command to execute
        :param inputs: List of input strings to provide
        :param timeout: Maximum time to wait for the program
        :return: ExecutionOutputData with collected stdout, stderr, and timeout status
        """
        try:
            # Join inputs with newlines - we still provide all inputs at once
            # but the program will consume them one by one when it calls input()
            input_str = "\n".join(inputs)
            
            process = subprocess.Popen(
                command,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,  # Use bytes for better control
            )

            try:
                # Provide all input at once and get output
                stdout_bytes, stderr_bytes = process.communicate(
                    input=input_str.encode(), timeout=timeout
                )
                
                # Decode output
                stdout = stdout_bytes.decode('utf-8')
                stderr = stderr_bytes.decode('utf-8')
                
                # Remove trailing newline that subprocess adds
                if stdout.endswith('\n'):
                    stdout = stdout[:-1]
                
                stdout = strip_carriage_return(stdout)
                stderr = strip_carriage_return(stderr)

                return ExecutionOutputData(stdout=stdout, stderr=stderr, timeout=False)

            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                return ExecutionOutputData(timeout=True)

        except Exception as e:
            return ExecutionOutputData(
                stdout="",
                stderr=f"Error during interactive execution: {str(e)}",
                timeout=False
            )

