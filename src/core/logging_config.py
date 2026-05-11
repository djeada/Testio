"""Centralised logging configuration for Testio.

Call ``configure_logging()`` once at application startup (server or CLI).
Subsequent ``logging.getLogger(__name__)`` calls automatically inherit the
configured handler and formatter.

Environment variables
---------------------
TESTIO_LOG_LEVEL : str
    Standard Python log-level name (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    Defaults to ``INFO``.
TESTIO_LOG_FORMAT : str
    ``json``  — emit structured JSON records (recommended for production).
    ``text``  — human-readable format (default for development/CLI).
"""

import logging
import os
import sys
from typing import Optional


def configure_logging(
    level: Optional[str] = None,
    json_format: Optional[bool] = None,
) -> None:
    """Configure the root logger.

    :param level: Log level name. Falls back to ``TESTIO_LOG_LEVEL`` env var,
        then ``INFO``.
    :param json_format: When ``True`` emit JSON lines; when ``False`` emit
        human-readable text.  Falls back to ``TESTIO_LOG_FORMAT == "json"``.
    """
    if level is None:
        level = os.environ.get("TESTIO_LOG_LEVEL", "INFO").upper()

    if json_format is None:
        json_format = os.environ.get("TESTIO_LOG_FORMAT", "text").lower() == "json"

    root = logging.getLogger()
    root.setLevel(level)

    # Remove pre-existing handlers to avoid duplicate output on re-configuration.
    for h in root.handlers[:]:
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if json_format:
        try:
            from pythonjsonlogger.json import JsonFormatter  # type: ignore[import-not-found]

            formatter: logging.Formatter = JsonFormatter(
                "%(asctime)s %(name)s %(levelname)s %(message)s",
                rename_fields={"levelname": "level", "asctime": "timestamp"},
            )
        except ImportError:  # fallback if package somehow not installed
            formatter = logging.Formatter(
                "%(asctime)s %(name)s %(levelname)s %(message)s"
            )
    else:
        formatter = logging.Formatter(
            "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )

    handler.setFormatter(formatter)
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger.

    Convenience wrapper so callers don't need to import ``logging`` directly.

    :param name: Typically ``__name__`` of the calling module.
    :return: Configured :class:`logging.Logger` instance.
    """
    return logging.getLogger(name)
