"""POSIX resource-limit sandbox for student code execution.

This is a best-effort defence layer, not an isolation boundary: it caps CPU
time, memory, written file size and core dumps for the child process. It does
not restrict filesystem or network access. Untrusted submissions should run
inside a container (see the Docker deployment docs) for real isolation.
"""

import os
import sys
from pathlib import Path
from typing import Callable, Optional, Sequence

if sys.platform != "win32":
    # Imported at module level on purpose: importing inside preexec_fn runs in
    # the forked child and can deadlock on the import lock when the parent is
    # multi-threaded (as the server is).
    import resource
else:  # pragma: no cover - Windows has no rlimits
    resource = None

# Runtimes that reserve very large virtual address ranges at startup (V8, JVM).
# RLIMIT_AS makes them abort before running a single line of user code, so the
# address-space cap is skipped for them; CPU/file limits and the wall-clock
# timeout still apply. Use container memory limits to bound these.
_ADDRESS_SPACE_HUNGRY = {"node", "nodejs", "java", "deno", "bun"}

_MAX_FILE_SIZE_BYTES = 64 * 1024 * 1024


def get_sandbox_cpu_secs() -> int:
    """CPU time limit for student code (seconds). 0 = disabled."""
    return int(os.environ.get("TESTIO_SANDBOX_CPU_SECS", "30"))


def get_sandbox_mem_mb() -> int:
    """Virtual memory limit for student code (MB). 0 = disabled."""
    return int(os.environ.get("TESTIO_SANDBOX_MEM_MB", "512"))


def _wants_address_space_limit(argv: Optional[Sequence[str]]) -> bool:
    if not argv:
        return True
    return Path(argv[0]).name.lower() not in _ADDRESS_SPACE_HUNGRY


def make_preexec_fn(
    cpu_secs: int = 30,
    mem_mb: int = 512,
    argv: Optional[Sequence[str]] = None,
) -> Optional[Callable[[], None]]:
    """Return a preexec_fn that applies POSIX resource limits, or None on non-POSIX."""
    if resource is None:
        return None

    limit_memory = mem_mb > 0 and _wants_address_space_limit(argv)

    def _apply_limits() -> None:
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        resource.setrlimit(
            resource.RLIMIT_FSIZE, (_MAX_FILE_SIZE_BYTES, _MAX_FILE_SIZE_BYTES)
        )
        if cpu_secs > 0:
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_secs, cpu_secs + 5))
        if limit_memory:
            mem_bytes = mem_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))

    return _apply_limits


def default_preexec_fn(
    argv: Optional[Sequence[str]] = None,
) -> Optional[Callable[[], None]]:
    """preexec_fn using the limits configured through the environment."""
    return make_preexec_fn(get_sandbox_cpu_secs(), get_sandbox_mem_mb(), argv)
