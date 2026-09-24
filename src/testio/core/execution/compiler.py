"""
Handles compilation of programs before execution.
Supports compiled languages like C, C++, Java, Go, Rust, etc.
"""

import atexit
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from .command_utils import format_command
from .process import run_process


class CompilationError(Exception):
    """Raised when compilation fails."""

    def __init__(self, stderr: str, returncode: int):
        self.stderr = stderr
        self.returncode = returncode
        super().__init__(f"Compilation failed with exit code {returncode}:\n{stderr}")


class Compiler:
    """Handles compilation of programs before they can be executed."""

    @staticmethod
    def _find_compiled_output(
        source_stem: str,
        source_name: str,
        output_dir: Path,
    ) -> Path:
        for artifact in sorted(output_dir.rglob("*")):
            if (
                artifact.is_file()
                and artifact.stem == source_stem
                and artifact.name != source_name
            ):
                return artifact
        return output_dir / source_stem

    def compile(
        self,
        compile_command: str,
        source_path: str,
        timeout: int = 30,
        output_dir: str | None = None,
    ) -> Optional[str]:
        """
        Compiles the source file using the provided compilation command.

        :param compile_command: The compilation command template (e.g., "gcc {source} -o {output}")
        :param source_path: Path to the source file
        :param timeout: Compilation timeout in seconds
        :param output_dir: Directory for compiled artifacts
        :return: Path to the compiled executable or None if compilation failed
        :raises CompilationError: If compilation fails
        """
        if not compile_command:
            return None

        source_path_obj = Path(source_path).resolve()
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
            atexit.register(shutil.rmtree, output_dir, ignore_errors=True)

        output_dir_path = Path(output_dir).resolve()
        output_dir_path.mkdir(parents=True, exist_ok=True)
        output_path = output_dir_path / source_path_obj.stem

        source_filename = source_path_obj.name
        command_cwd = source_path_obj.parent

        if "{output}" not in compile_command:
            copied_source = output_dir_path / source_filename
            if copied_source != source_path_obj:
                shutil.copy2(source_path_obj, copied_source)
            command_cwd = output_dir_path

        command = format_command(
            compile_command,
            source=source_filename,
            output=str(output_path),
        )

        try:
            # Compilers are trusted tools and can legitimately need more memory
            # than the student-code sandbox allows, so rlimits are not applied.
            result = run_process(
                command,
                timeout=timeout,
                cwd=str(command_cwd),
                sandbox=False,
            )
        except OSError as exc:
            raise CompilationError(str(exc), -1) from exc

        if result.timed_out:
            raise CompilationError(
                f"Compilation timed out after {timeout} seconds",
                -1,
            )
        if result.returncode != 0:
            raise CompilationError(result.stderr or result.stdout, result.returncode)

        return str(
            self._find_compiled_output(
                source_path_obj.stem,
                source_path_obj.name,
                output_dir_path,
            )
        )
