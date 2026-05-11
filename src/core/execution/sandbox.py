"""POSIX resource-limit sandbox for student code execution."""

import sys
from typing import Callable, Optional


def make_preexec_fn(cpu_secs: int = 30, mem_mb: int = 512) -> Optional[Callable]:
    """Return a preexec_fn that applies POSIX resource limits, or None on non-POSIX."""
    if sys.platform == "win32":
        return None
    if cpu_secs <= 0 and mem_mb <= 0:
        return None

    def _apply_limits() -> None:
        import resource  # noqa: PLC0415

        if cpu_secs > 0:
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_secs, cpu_secs + 5))
        if mem_mb > 0:
            mem_bytes = mem_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))

    return _apply_limits
