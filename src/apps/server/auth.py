"""API-key authentication dependency for teacher-only endpoints."""

import logging
import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

logger = logging.getLogger("testio.auth")

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_teacher_auth(api_key: str | None = Security(_API_KEY_HEADER)) -> None:
    """FastAPI dependency that enforces an API key on teacher-only routes.

    Configure by setting the ``TESTIO_TEACHER_API_KEY`` environment variable.
    If the variable is not set the server runs in **open dev mode** and all
    requests are allowed (a warning is logged once at startup).
    """
    expected = os.environ.get("TESTIO_TEACHER_API_KEY", "")
    if not expected:
        return
    if api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
