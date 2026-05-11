"""Environment-backed settings helpers for the server."""

import os

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


def get_sandbox_cpu_secs() -> int:
    """CPU time limit for student code (seconds). 0 = disabled."""
    return int(os.environ.get("TESTIO_SANDBOX_CPU_SECS", "30"))


def get_sandbox_mem_mb() -> int:
    """Virtual memory limit for student code (MB). 0 = disabled."""
    return int(os.environ.get("TESTIO_SANDBOX_MEM_MB", "512"))


def get_log_level() -> str:
    """Log level name (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: INFO."""
    return os.environ.get("TESTIO_LOG_LEVEL", "INFO").upper()


def get_log_format() -> str:
    """Log output format: 'json' (structured) or 'text' (human-readable). Default: text."""
    return os.environ.get("TESTIO_LOG_FORMAT", "text").lower()

