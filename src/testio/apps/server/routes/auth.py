"""Teacher login/logout for the web UI.

``POST /api/auth/login`` exchanges the teacher API key for an HttpOnly,
SameSite=Strict session cookie, so the browser never has to keep the key in
JavaScript-readable storage. API clients can keep sending ``X-API-Key``.
"""

import os
from typing import Dict, Union

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from testio.apps.server.auth import (
    SESSION_COOKIE_NAME,
    api_key_matches,
    auth_mode,
    get_session_ttl_seconds,
    get_teacher_api_key,
    is_teacher_request,
    make_session_token,
)

auth_router: APIRouter = APIRouter(tags=["Auth"])


class LoginRequest(BaseModel):
    """Teacher login payload."""

    api_key: str = Field(..., min_length=1, max_length=1024)


def _secure_cookie(request: Request) -> bool:
    configured = os.environ.get("TESTIO_SECURE_COOKIES", "").strip().lower()
    if configured in {"1", "true", "yes", "on"}:
        return True
    if configured in {"0", "false", "no", "off"}:
        return False
    return request.url.scheme == "https"


@auth_router.post("/api/auth/login")
def login(
    request: Request, payload: LoginRequest, response: Response
) -> Dict[str, bool]:
    """Validate the teacher key and set the session cookie."""
    if auth_mode() != "key":
        raise HTTPException(
            status_code=400,
            detail="This server has no teacher API key configured "
            "(TESTIO_TEACHER_API_KEY), so there is nothing to log in with.",
        )
    if not api_key_matches(payload.api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    ttl = get_session_ttl_seconds()
    response.set_cookie(
        SESSION_COOKIE_NAME,
        make_session_token(get_teacher_api_key(), ttl),
        max_age=ttl,
        httponly=True,
        samesite="strict",
        secure=_secure_cookie(request),
        path="/",
    )
    return {"authenticated": True}


@auth_router.post("/api/auth/logout")
def logout(response: Response) -> Dict[str, bool]:
    """Clear the session cookie."""
    response.delete_cookie(SESSION_COOKIE_NAME, path="/", samesite="strict")
    return {"authenticated": False}


@auth_router.get("/api/auth/status")
def auth_status(request: Request) -> Dict[str, Union[bool, str]]:
    """Whether the caller is authenticated as a teacher, and how auth is set up."""
    return {"authenticated": is_teacher_request(request), "mode": auth_mode()}


@auth_router.get("/login", response_class=HTMLResponse)
def login_page(request: Request) -> HTMLResponse:
    """Teacher login form."""
    templates = request.app.state.templates
    mode = getattr(request.app.state, "mode", "teacher")
    return templates.TemplateResponse(
        request, "login.html", {"mode": mode, "auth_mode": auth_mode()}
    )
