"""Tests for teacher authentication (API key header, login cookie, fail-closed)."""

import time

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from testio.apps.server.auth import (
    SESSION_COOKIE_NAME,
    make_session_token,
    require_teacher_auth,
    verify_session_token,
)

from .conftest import TEACHER_KEY


def create_test_app() -> FastAPI:
    """Create a minimal app with a protected route."""
    app = FastAPI()

    @app.get("/protected")
    def protected(_auth: None = Depends(require_teacher_auth)) -> dict[str, str]:
        return {"status": "ok"}

    return app


def test_protected_route_rejects_wrong_api_key(monkeypatch):
    """Protected routes should reject incorrect API keys."""
    monkeypatch.setenv("TESTIO_TEACHER_API_KEY", "secret-key")

    with TestClient(create_test_app()) as client:
        response = client.get("/protected", headers={"X-API-Key": "wrong-key"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"


def test_protected_route_accepts_correct_api_key(monkeypatch):
    """Protected routes should allow the configured API key."""
    monkeypatch.setenv("TESTIO_TEACHER_API_KEY", "secret-key")

    with TestClient(create_test_app()) as client:
        response = client.get("/protected", headers={"X-API-Key": "secret-key"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_protected_route_fails_closed_without_key(monkeypatch):
    """No key configured and not bound to loopback: teacher routes are refused."""
    monkeypatch.delenv("TESTIO_TEACHER_API_KEY", raising=False)
    monkeypatch.setenv("TESTIO_BIND_HOST", "0.0.0.0")

    with TestClient(create_test_app(), client=("127.0.0.1", 5000)) as client:
        response = client.get("/protected")

    assert response.status_code == 401
    assert "not configured" in response.json()["detail"]


def test_insecure_flag_allows_requests_without_key(monkeypatch):
    monkeypatch.delenv("TESTIO_TEACHER_API_KEY", raising=False)
    monkeypatch.setenv("TESTIO_INSECURE_NO_AUTH", "1")

    with TestClient(create_test_app()) as client:
        assert client.get("/protected").status_code == 200


def test_loopback_bind_allows_direct_local_requests_only(monkeypatch):
    monkeypatch.delenv("TESTIO_TEACHER_API_KEY", raising=False)
    monkeypatch.setenv("TESTIO_BIND_HOST", "127.0.0.1")
    app = create_test_app()

    with TestClient(app, client=("127.0.0.1", 5000)) as client:
        assert client.get("/protected").status_code == 200
        # A local reverse proxy forwards remote clients from loopback.
        forwarded = client.get("/protected", headers={"X-Forwarded-For": "203.0.113.9"})
        assert forwarded.status_code == 401

    with TestClient(app, client=("192.0.2.10", 5000)) as client:
        assert client.get("/protected").status_code == 401


def test_session_token_round_trip_and_expiry():
    token = make_session_token("k", ttl_seconds=60)
    assert verify_session_token("k", token)
    assert not verify_session_token("other-key", token)
    assert not verify_session_token("k", token + "0")
    expired = f"{int(time.time()) - 1}.{token.split('.', 1)[1]}"
    assert not verify_session_token("k", expired)
    assert not verify_session_token("k", None)


def test_login_cookie_grants_access(anon_client):
    assert anon_client.get("/student_submissions").status_code == 401

    bad = anon_client.post("/api/auth/login", json={"api_key": "nope"})
    assert bad.status_code == 401

    good = anon_client.post("/api/auth/login", json={"api_key": TEACHER_KEY})
    assert good.status_code == 200
    set_cookie = good.headers["set-cookie"].lower()
    assert SESSION_COOKIE_NAME in set_cookie
    assert "httponly" in set_cookie
    assert "samesite=strict" in set_cookie

    assert anon_client.get("/student_submissions").status_code == 200
    assert anon_client.get("/api/auth/status").json()["authenticated"] is True

    anon_client.post("/api/auth/logout")
    anon_client.cookies.clear()
    assert anon_client.get("/student_submissions").status_code == 401


def test_teacher_pages_redirect_to_login(anon_client, teacher_client):
    response = anon_client.get("/homework", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].startswith("/login?next=")
    assert anon_client.get("/login").status_code == 200
    assert teacher_client.get("/homework").status_code == 200
