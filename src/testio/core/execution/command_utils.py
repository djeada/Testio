"""Helpers for validating and building command-line invocations.

The executable allow-list stops configs from naming arbitrary system binaries
(``/bin/sh -c ...``). It is a guard-rail, not a sandbox: the programs under
test run arbitrary code by design, so deployments accepting untrusted
submissions must isolate execution (see SECURITY.md).
"""

from __future__ import annotations

import os
import shlex
from pathlib import Path, PurePosixPath

ALLOWED_EXECUTABLES = {
    "python",
    "python2",
    "python3",
    "node",
    "nodejs",
    "ruby",
    "perl",
    "java",
    "javac",
    "go",
    "gcc",
    "g++",
    "clang",
    "rustc",
}

SUFFIX_BY_EXECUTABLE = {
    "python": ".py",
    "python2": ".py",
    "python3": ".py",
    "node": ".js",
    "nodejs": ".js",
    "ruby": ".rb",
    "perl": ".pl",
    "java": ".java",
    "javac": ".java",
    "go": ".go",
    "gcc": ".c",
    "clang": ".c",
    "g++": ".cpp",
    "rustc": ".rs",
}


def _split_tokens(command: str) -> list[str]:
    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        raise ValueError(f"Invalid command syntax: {exc}") from exc

    if not tokens:
        raise ValueError("Command cannot be empty")

    return tokens


def get_allowed_executables() -> set[str]:
    """Built-in allow-list plus extras from TESTIO_ALLOWED_EXECUTABLES (comma list)."""
    extra = os.environ.get("TESTIO_ALLOWED_EXECUTABLES", "")
    return ALLOWED_EXECUTABLES | {
        name.strip().lower() for name in extra.split(",") if name.strip()
    }


def _is_local_executable(token: str) -> bool:
    """``./prog`` or a compile placeholder such as ``{output}`` / ``./{output}``."""
    if token.startswith("{") or token.startswith("./{"):
        return True
    if not token.startswith("./"):
        return False
    return ".." not in PurePosixPath(token.replace("\\", "/")).parts


def validate_command_template(command: str, field_name: str = "command") -> str:
    """Validate a command template before it is executed."""
    normalized_command = command.strip()
    if not normalized_command:
        raise ValueError(f"{field_name.replace('_', ' ').capitalize()} cannot be empty")

    tokens = _split_tokens(normalized_command)
    executable = Path(tokens[0]).name.lower()

    if executable not in get_allowed_executables() and not _is_local_executable(
        tokens[0]
    ):
        raise ValueError(f"Unsupported executable in {field_name}: {tokens[0]}")

    return normalized_command


def split_command(command: str) -> list[str]:
    """Convert a command string into argv tokens.

    Commands reaching this point are built by ``build_run_command`` from a
    template that was validated when the config was parsed; the appended
    target may itself be an executable (e.g. a compiled binary), so the
    allow-list is not re-applied here.
    """
    return _split_tokens(command)


def format_command(template: str, **replacements: str) -> list[str]:
    """Apply placeholder replacements to a command template and return argv."""
    tokens = _split_tokens(validate_command_template(template))
    return [token.format(**replacements) for token in tokens]


def build_run_command(command_template: str, target_path: str) -> str:
    """Build the shell-safe command that runs ``target_path``.

    Without placeholders the target is appended (``python3`` -> ``python3 prog.py``).
    A template may instead place it explicitly using ``{output}`` (the full
    path), ``{dir}`` (its directory) and ``{stem}`` (file name without
    extension), e.g. ``java -cp {dir} {stem}`` for a compiled Java class.
    """
    if not command_template:
        return shlex.join([target_path])

    tokens = _split_tokens(validate_command_template(command_template))
    if any("{" in token for token in tokens):
        target = Path(target_path)
        replacements = {
            "output": str(target),
            "dir": str(target.parent),
            "stem": target.stem,
        }
        try:
            return shlex.join([token.format(**replacements) for token in tokens])
        except (KeyError, IndexError, ValueError) as exc:
            raise ValueError(
                f"Unknown placeholder in run command {command_template!r}: {exc}"
            ) from exc

    tokens.append(target_path)
    return shlex.join(tokens)


def replace_command_path(command: str, original_path: str, new_path: str) -> str:
    """Replace the path token inside an existing command string."""
    original = Path(original_path).resolve(strict=False)
    updated_tokens = []
    replaced = False

    for token in _split_tokens(command):
        token_path = Path(token)
        if token == original_path or token_path.resolve(strict=False) == original:
            updated_tokens.append(new_path)
            replaced = True
        else:
            updated_tokens.append(token)

    if not replaced:
        raise ValueError(f"Command does not reference expected path: {original_path}")

    return shlex.join(updated_tokens)


def infer_source_suffix(
    *,
    filename: str = "",
    command: str = "",
    compile_command: str = "",
    path: str = "",
) -> str:
    """Best-effort source suffix inference for temporary submission files."""
    for candidate in (filename, path):
        suffix = Path(candidate).suffix
        if suffix:
            return suffix

    for template in (compile_command, command):
        if not template:
            continue
        try:
            executable = Path(_split_tokens(template)[0]).name.lower()
        except ValueError:
            continue
        suffix = SUFFIX_BY_EXECUTABLE.get(executable)
        if suffix:
            return suffix

    return ".txt"
