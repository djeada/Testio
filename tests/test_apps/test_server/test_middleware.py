"""Tests for RequestLoggingMiddleware."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.apps.server.middleware import RequestLoggingMiddleware


@pytest.fixture
def app_with_middleware():
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/ping")
    def ping():
        return {"pong": True}

    return app


def test_middleware_passes_request(app_with_middleware):
    """Middleware should not block normal requests."""
    client = TestClient(app_with_middleware)
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"pong": True}


def test_middleware_handles_404(app_with_middleware):
    """Middleware should pass through 404s."""
    client = TestClient(app_with_middleware)
    response = client.get("/nonexistent")
    assert response.status_code == 404
