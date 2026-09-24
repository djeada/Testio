"""Shared fixtures for the server tests.

Every test runs with its own SQLite databases (never the repository's
``testio.db`` / ``test.db``), a configured teacher API key, and rate limiting
disabled unless a test opts back in.
"""

import pytest
from fastapi.testclient import TestClient

TEACHER_KEY = "test-teacher-key"


@pytest.fixture(autouse=True)
def _isolated_server_env(tmp_path, monkeypatch):
    monkeypatch.setenv("TESTIO_APP_DB_PATH", str(tmp_path / "app.db"))
    monkeypatch.setenv("TESTIO_CONFIG_DB_PATH", str(tmp_path / "config.db"))
    monkeypatch.setenv("TESTIO_TEACHER_API_KEY", TEACHER_KEY)
    monkeypatch.setenv("TESTIO_RATE_LIMIT_PER_MINUTE", "0")
    monkeypatch.delenv("TESTIO_INSECURE_NO_AUTH", raising=False)
    monkeypatch.delenv("TESTIO_BIND_HOST", raising=False)
    # Cached config lookups must not leak between tests' databases.
    from testio.apps.server.database.configuration_data import (
        load_suite_config_json,
        parse_config_data,
    )

    parse_config_data.invalidate()
    load_suite_config_json.invalidate()
    yield
    parse_config_data.invalidate()
    load_suite_config_json.invalidate()


@pytest.fixture
def teacher_headers():
    return {"X-API-Key": TEACHER_KEY}


@pytest.fixture
def teacher_app():
    from testio.apps.server.app.testio_server import create_app

    return create_app(mode="teacher")


@pytest.fixture
def teacher_client(teacher_app, teacher_headers):
    """Client that authenticates as the teacher on every request."""
    with TestClient(teacher_app, headers=teacher_headers) as client:
        yield client


@pytest.fixture
def anon_client(teacher_app):
    """Client without any credentials (a student / attacker)."""
    with TestClient(teacher_app) as client:
        yield client
