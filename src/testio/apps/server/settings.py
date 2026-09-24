"""Environment-backed settings helpers for the server."""

import os

# Re-exported for backward compatibility.
from testio.core.execution.sandbox import (  # noqa: F401
    get_sandbox_cpu_secs,
    get_sandbox_mem_mb,
)

APP_DATABASE_PATH_ENV = "TESTIO_APP_DB_PATH"
CONFIG_DATABASE_PATH_ENV = "TESTIO_CONFIG_DB_PATH"

DEFAULT_APP_DATABASE_PATH = "testio.db"
DEFAULT_CONFIG_DATABASE_PATH = "test.db"


def get_app_database_path() -> str:
    """Return the configured application database path."""
    return os.getenv(APP_DATABASE_PATH_ENV, DEFAULT_APP_DATABASE_PATH)


def get_config_database_path() -> str:
    """Return the configured config-storage database path."""
    return os.getenv(CONFIG_DATABASE_PATH_ENV, DEFAULT_CONFIG_DATABASE_PATH)


def get_max_upload_size_mb() -> int:
    """Max upload file size in MB. 0 = no limit."""
    return int(os.environ.get("TESTIO_MAX_UPLOAD_SIZE_MB", "10"))


def get_log_level() -> str:
    """Log level name (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: INFO."""
    return os.environ.get("TESTIO_LOG_LEVEL", "INFO").upper()


def get_log_format() -> str:
    """Log output format: 'json' (structured) or 'text' (human-readable). Default: text."""
    return os.environ.get("TESTIO_LOG_FORMAT", "text").lower()


def _env_number(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


def get_max_upload_bytes() -> int:
    """Per-file upload limit in bytes (TESTIO_MAX_UPLOAD_SIZE_MB). 0 = no limit."""
    return int(_env_number("TESTIO_MAX_UPLOAD_SIZE_MB", 10) * 1024 * 1024)


def get_max_request_bytes() -> int:
    """Whole-request body limit (TESTIO_MAX_REQUEST_SIZE_MB, default 50). 0 = none."""
    return int(_env_number("TESTIO_MAX_REQUEST_SIZE_MB", 50) * 1024 * 1024)


def get_max_upload_files() -> int:
    """Maximum number of student files per homework request (default 200)."""
    return int(_env_number("TESTIO_MAX_UPLOAD_FILES", 200))


def get_rate_limit_per_minute() -> int:
    """Requests per client per minute (TESTIO_RATE_LIMIT_PER_MINUTE, default 120).

    0 disables rate limiting.
    """
    return int(_env_number("TESTIO_RATE_LIMIT_PER_MINUTE", 120))
