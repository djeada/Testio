"""Basic tests for the ConnectionPool."""

import pytest

from src.apps.server.database.connection_pool import (
    close_all_pools,
    get_connection_pool,
)


@pytest.fixture(autouse=True)
def cleanup_pools():
    yield
    close_all_pools()


def test_get_connection_pool_returns_pool(tmp_path):
    db_path = str(tmp_path / "test.db")
    pool = get_connection_pool(db_path)
    assert pool is not None


def test_pool_is_singleton_per_path(tmp_path):
    db_path = str(tmp_path / "test.db")
    pool1 = get_connection_pool(db_path)
    pool2 = get_connection_pool(db_path)
    assert pool1 is pool2


def test_execute_and_query(tmp_path):
    db_path = str(tmp_path / "test.db")
    pool = get_connection_pool(db_path)
    with pool.get_connection() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, val TEXT)")
        conn.execute("INSERT INTO t (val) VALUES (?)", ("hello",))
        conn.commit()
    with pool.get_connection() as conn:
        cursor = conn.execute("SELECT val FROM t")
        rows = cursor.fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "hello"


def test_foreign_keys_enabled(tmp_path):
    db_path = str(tmp_path / "test.db")
    pool = get_connection_pool(db_path)
    with pool.get_connection() as conn:
        cursor = conn.execute("PRAGMA foreign_keys")
        assert cursor.fetchone()[0] == 1
