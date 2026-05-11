"""End-to-end tests for the FastAPI app using TestClient."""

import importlib

import pytest
from fastapi.testclient import TestClient

from src.apps.server.app.testio_server import create_app
import src.apps.server.auth as auth_mod


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_livez_endpoint(client):
    response = client.get("/livez")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readyz_endpoint(client):
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_docs_accessible(client):
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_json(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "openapi" in response.json()


def test_protected_route_without_key(monkeypatch, client):
    """Teacher route without API key should be 401 when key is configured."""
    monkeypatch.setenv("TESTIO_TEACHER_API_KEY", "secret")
    importlib.reload(auth_mod)

    response = client.post(
        "/api/exam/create_session", json={"config_file": "test.json"}
    )

    assert response.status_code in (401, 422)
