"""Authentication for teacher-only endpoints.

Teachers authenticate with the key in ``TESTIO_TEACHER_API_KEY``, either

* per request, with an ``X-API-Key`` header (scripts / API clients), or
* once, through ``POST /api/auth/login``, which sets an HttpOnly,
  SameSite=Strict session cookie used by the web UI.

When no key is configured the server fails **closed**: teacher endpoints are
refused, except

* when ``TESTIO_INSECURE_NO_AUTH=1`` is set (explicit development opt-out), or
* when the server is bound to a loopback address (``TESTIO_BIND_HOST``, set by
  ``testio-server --host``) *and* the request comes directly from loopback
  without proxy forwarding headers - i.e. a single-user local setup.
"""

import hashlib
import hmac
import ipaddress
import logging
import os
import time
from typing import Optional
from urllib.parse import quote

from fastapi import HTTPException, Request, Security, status
from fastapi.responses import RedirectResponse
from fastapi.security import APIKeyHeader

logger = logging.getLogger("testio.auth")

API_KEY_ENV = "TESTIO_TEACHER_API_KEY"
INSECURE_NO_AUTH_ENV = "TESTIO_INSECURE_NO_AUTH"
BIND_HOST_ENV = "TESTIO_BIND_HOST"
SESSION_TTL_ENV = "TESTIO_SESSION_TTL_HOURS"

SESSION_COOKIE_NAME = "testio_teacher_session"

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
_FORWARDING_HEADERS = ("x-forwarded-for", "forwarded", "x-real-ip")
_TRUE_VALUES = {"1", "true", "yes", "on"}


def get_teacher_api_key() -> str:
    """The configured teacher key, or an empty string when unset."""
    return os.environ.get(API_KEY_ENV, "")


def insecure_no_auth_enabled() -> bool:
    """True when the operator explicitly disabled teacher authentication."""
    return os.environ.get(INSECURE_NO_AUTH_ENV, "").strip().lower() in _TRUE_VALUES


def get_session_ttl_seconds() -> int:
    """Lifetime of a teacher login cookie (TESTIO_SESSION_TTL_HOURS, default 12)."""
    try:
        hours = float(os.environ.get(SESSION_TTL_ENV, "12"))
    except ValueError:
        hours = 12.0
    return max(60, int(hours * 3600))


def _is_loopback(host: Optional[str]) -> bool:
    if not host:
        return False
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host.strip("[]")).is_loopback
    except ValueError:
        return False


def bound_to_loopback() -> bool:
    """True when the server was started on a loopback interface only."""
    return _is_loopback(os.environ.get(BIND_HOST_ENV, ""))


def auth_mode() -> str:
    """``"key"`` (key configured), ``"open"`` (explicitly disabled),
    ``"local"`` (no key, loopback bind) or ``"closed"`` (no key: refuse)."""
    if get_teacher_api_key():
        return "key"
    if insecure_no_auth_enabled():
        return "open"
    if bound_to_loopback():
        return "local"
    return "closed"


def log_auth_configuration() -> None:
    """Emit a startup message describing how teacher endpoints are protected."""
    mode = auth_mode()
    if mode == "open":
        logger.warning(
            "!!! %s is set: teacher endpoints are UNAUTHENTICATED. Anyone who can "
            "reach this server can run arbitrary code on it. Development only. !!!",
            INSECURE_NO_AUTH_ENV,
        )
    elif mode == "local":
        logger.warning(
            "%s is not set: teacher endpoints are only available to direct "
            "loopback requests. Set a key before exposing the server.",
            API_KEY_ENV,
        )
    elif mode == "closed":
        logger.warning(
            "%s is not set: teacher endpoints are DISABLED. Set %s (or %s=1 for "
            "local development) to enable them.",
            API_KEY_ENV,
            API_KEY_ENV,
            INSECURE_NO_AUTH_ENV,
        )


# ----------------------------------------------------------------------
# Session cookie tokens: "<expiry>.<hmac(key, expiry)>". Stateless, so they
# work across worker processes and are invalidated by rotating the key.
# ----------------------------------------------------------------------


def _sign(key: str, payload: str) -> str:
    return hmac.new(
        key.encode("utf-8"), f"testio-teacher:{payload}".encode("utf-8"), hashlib.sha256
    ).hexdigest()


def make_session_token(key: str, ttl_seconds: Optional[int] = None) -> str:
    """Create a signed teacher session token valid for ``ttl_seconds``."""
    expires = int(time.time()) + (ttl_seconds or get_session_ttl_seconds())
    return f"{expires}.{_sign(key, str(expires))}"


def verify_session_token(key: str, token: Optional[str]) -> bool:
    """Check a session token's signature and expiry (constant-time compare)."""
    if not key or not token or "." not in token:
        return False
    expires, _, signature = token.partition(".")
    if not expires.isdigit() or int(expires) < time.time():
        return False
    return hmac.compare_digest(signature, _sign(key, expires))


def api_key_matches(candidate: Optional[str]) -> bool:
    """Constant-time comparison of ``candidate`` with the configured key."""
    expected = get_teacher_api_key()
    if not expected or not candidate:
        return False
    return hmac.compare_digest(candidate.encode("utf-8"), expected.encode("utf-8"))


def _is_direct_loopback_request(request: Request) -> bool:
    client_host = request.client.host if request.client else None
    if not _is_loopback(client_host):
        return False
    # A local reverse proxy connects from loopback too; its forwarding
    # headers show the request really came from elsewhere.
    return not any(request.headers.get(name) for name in _FORWARDING_HEADERS)


def is_teacher_request(request: Request, api_key: Optional[str] = None) -> bool:
    """Whether ``request`` carries valid teacher credentials (or needs none)."""
    mode = auth_mode()
    if mode == "open":
        return True
    if mode == "local":
        return _is_direct_loopback_request(request)
    if mode == "closed":
        return False

    if api_key is None:
        api_key = request.headers.get("X-API-Key")
    if api_key_matches(api_key):
        return True
    return verify_session_token(
        get_teacher_api_key(), request.cookies.get(SESSION_COOKIE_NAME)
    )


def require_teacher_auth(
    request: Request,
    api_key: Optional[str] = Security(_API_KEY_HEADER),
) -> None:
    """FastAPI dependency that enforces teacher authentication.

    :raises HTTPException 401: when the request is not authenticated.
    """
    if is_teacher_request(request, api_key):
        return

    if auth_mode() == "key":
        detail = "Invalid or missing API key"
    else:
        detail = (
            "Teacher authentication is not configured on this server: "
            f"set {API_KEY_ENV}"
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "ApiKey"},
    )


def teacher_page_redirect(request: Request) -> Optional[RedirectResponse]:
    """For teacher HTML pages: a redirect to the login page when the browser
    is not authenticated, else None."""
    if is_teacher_request(request):
        return None
    target = request.url.path
    if request.url.query:
        target = f"{target}?{request.url.query}"
    return RedirectResponse(
        url=f"/login?next={quote(target, safe='')}", status_code=303
    )
