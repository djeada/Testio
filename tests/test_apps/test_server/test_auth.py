"""Tests for teacher API-key authentication."""

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from src.apps.server.auth import require_teacher_auth


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


def test_protected_route_allows_requests_in_dev_mode(monkeypatch):
    """Protected routes should allow requests when no API key is configured."""
    monkeypatch.delenv("TESTIO_TEACHER_API_KEY", raising=False)

    with TestClient(create_test_app()) as client:
        response = client.get("/protected")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
