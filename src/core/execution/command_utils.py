"""Helpers for validating and building command-line invocations."""

from __future__ import annotations

import shlex
from pathlib import Path

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


def _is_local_executable(token: str) -> bool:
    executable_path = Path(token)
    return executable_path.is_absolute() or token.startswith((".", ".."))


def validate_command_template(command: str, field_name: str = "command") -> str:
    """Validate a command template before it is executed."""
    normalized_command = command.strip()
    if not normalized_command:
        raise ValueError(f"{field_name.replace('_', ' ').capitalize()} cannot be empty")

    tokens = _split_tokens(normalized_command)
    executable = Path(tokens[0]).name.lower()

    if executable not in ALLOWED_EXECUTABLES and not _is_local_executable(tokens[0]):
        raise ValueError(f"Unsupported executable in {field_name}: {tokens[0]}")

    return normalized_command


def split_command(command: str) -> list[str]:
    """Convert a validated command string into argv tokens."""
    return _split_tokens(validate_command_template(command))


def format_command(template: str, **replacements: str) -> list[str]:
    """Apply placeholder replacements to a command template and return argv."""
    tokens = _split_tokens(validate_command_template(template))
    return [token.format(**replacements) for token in tokens]


def build_run_command(command_template: str, target_path: str) -> str:
    """Append a target path to an interpreter command and return a shell-safe string."""
    if not command_template:
        return shlex.join([target_path])

    tokens = _split_tokens(validate_command_template(command_template))
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
