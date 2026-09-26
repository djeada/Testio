"""
Robust subprocess execution shared by the runners and the compiler.

Guarantees provided here, which a bare ``subprocess.run`` does not give:

* the whole process tree is killed on timeout (and after normal exit), so
  programs that fork cannot leave orphans behind or keep pipes open;
* captured output is capped, so a program printing in an infinite loop cannot
  exhaust the memory of the process running the tests;
* output is decoded leniently, so invalid UTF-8 never crashes the tester;
* the exit code is reported, so crashes are detectable even without stderr.
"""

from __future__ import annotations

import os
import signal
import subprocess
import threading
from dataclasses import dataclass
from typing import IO, Dict, List, Optional, Sequence

from .sandbox import default_preexec_fn

_POSIX = os.name == "posix"
_CHUNK_SIZE = 64 * 1024


# Variables a child legitimately needs to find toolchains and behave sanely.
# Everything else (API keys, DB paths, cloud credentials...) is withheld so
# the code under test cannot read the host's secrets from its environment.
_ENV_ALLOWLIST = {
    "PATH",
    "HOME",
    "USER",
    "LANG",
    "LANGUAGE",
    "TZ",
    "TMPDIR",
    "TEMP",
    "TMP",
    "TERM",
    "JAVA_HOME",
    "GOROOT",
    "GOPATH",
    "GOCACHE",
    "CARGO_HOME",
    "RUSTUP_HOME",
    "NODE_PATH",
    "PYTHONPATH",
    "PYTHONIOENCODING",
    "VIRTUAL_ENV",
    "SYSTEMROOT",
    "COMSPEC",
    "PATHEXT",
    "WINDIR",
}


def build_child_env() -> Dict[str, str]:
    """Environment for child processes: allow-listed variables only.

    Extra names can be passed through with TESTIO_PASSTHROUGH_ENV (comma list).
    """
    extra = {
        name.strip()
        for name in os.environ.get("TESTIO_PASSTHROUGH_ENV", "").split(",")
        if name.strip()
    }
    allowed = _ENV_ALLOWLIST | extra
    return {
        key: value
        for key, value in os.environ.items()
        if key in allowed or key.startswith("LC_")
    }


def get_max_output_bytes() -> int:
    """Per-stream capture limit in bytes (TESTIO_MAX_OUTPUT_KB, default 1 MiB)."""
    return int(os.environ.get("TESTIO_MAX_OUTPUT_KB", "1024")) * 1024


@dataclass
class ProcessResult:
    stdout: str = ""
    stderr: str = ""
    returncode: Optional[int] = None
    timed_out: bool = False
    output_truncated: bool = False


class _CappedReader(threading.Thread):
    """Drains a pipe into memory, keeping at most ``limit`` bytes."""

    def __init__(self, stream: IO[bytes], limit: int, on_overflow) -> None:
        super().__init__(daemon=True)
        self._stream = stream
        self._limit = limit
        self._on_overflow = on_overflow
        self._chunks: List[bytes] = []
        self._size = 0
        self.truncated = False

    def run(self) -> None:
        try:
            while True:
                chunk = self._stream.read1(_CHUNK_SIZE)  # type: ignore[attr-defined]
                if not chunk:
                    break
                remaining = self._limit - self._size
                if remaining > 0:
                    self._chunks.append(chunk[:remaining])
                    self._size += min(len(chunk), remaining)
                if len(chunk) > remaining and not self.truncated:
                    self.truncated = True
                    self._on_overflow()
        except (OSError, ValueError):
            pass
        finally:
            try:
                self._stream.close()
            except OSError:
                pass

    def text(self) -> str:
        return b"".join(self._chunks).decode("utf-8", errors="replace")


def _kill_tree(process: subprocess.Popen) -> None:
    if _POSIX:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    else:  # pragma: no cover - Windows
        try:
            process.kill()
        except OSError:
            pass


def _feed_stdin(stream: IO[bytes], data: bytes) -> None:
    try:
        if data:
            stream.write(data)
    except (BrokenPipeError, OSError, ValueError):
        # The program exited (or closed stdin) without reading all input.
        pass
    finally:
        try:
            stream.close()
        except (BrokenPipeError, OSError):
            pass


def run_process(
    argv: Sequence[str],
    input_text: str = "",
    timeout: Optional[float] = None,
    cwd: Optional[str] = None,
    sandbox: bool = True,
    max_output_bytes: Optional[int] = None,
) -> ProcessResult:
    """
    Run ``argv`` to completion and capture its output.

    :raises OSError: if the executable cannot be started.
    """
    limit = get_max_output_bytes() if max_output_bytes is None else max_output_bytes
    popen_kwargs = {}
    if _POSIX:
        popen_kwargs["start_new_session"] = True
        if sandbox:
            popen_kwargs["preexec_fn"] = default_preexec_fn(argv)

    process = subprocess.Popen(
        list(argv),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        env=build_child_env(),
        **popen_kwargs,
    )

    overflowed = threading.Event()

    def on_overflow() -> None:
        overflowed.set()
        _kill_tree(process)

    readers = [
        _CappedReader(process.stdout, limit, on_overflow),
        _CappedReader(process.stderr, limit, on_overflow),
    ]
    for reader in readers:
        reader.start()

    feeder = threading.Thread(
        target=_feed_stdin,
        args=(process.stdin, input_text.encode("utf-8")),
        daemon=True,
    )
    feeder.start()

    timed_out = False
    try:
        process.wait(timeout=timeout if timeout and timeout > 0 else None)
    except subprocess.TimeoutExpired:
        timed_out = True
    finally:
        # Also reaps grandchildren that would otherwise hold the pipes open.
        _kill_tree(process)
        process.wait()
        for reader in readers:
            reader.join(timeout=5)
        feeder.join(timeout=1)

    return ProcessResult(
        stdout=readers[0].text(),
        stderr=readers[1].text(),
        returncode=process.returncode,
        timed_out=timed_out,
        output_truncated=overflowed.is_set(),
    )
