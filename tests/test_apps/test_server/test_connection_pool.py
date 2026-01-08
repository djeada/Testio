"""Tests for the connection pool module."""
import sys
import threading
import time

sys.path.append(".")

import pytest

from src.apps.server.database.connection_pool import (
    ConnectionPool,
    PoolConfig,
    PooledConnection,
    get_connection_pool,
    close_all_pools
)


class TestConnectionPool:
    """Test suite for ConnectionPool class."""

    @pytest.fixture
    def pool(self, tmp_path):
        """Create a temporary connection pool for testing."""
        db_path = str(tmp_path / "test.db")
        config = PoolConfig(min_connections=2, max_connections=5)
        pool = ConnectionPool(db_path, config)
        yield pool
        pool.close()

    def test_acquire_and_release(self, pool):
        """Test acquiring and releasing a connection."""
        conn = pool.acquire()
        assert isinstance(conn, PooledConnection)
        pool.release(conn)

    def test_connection_executes_sql(self, pool):
        """Test that connections can execute SQL."""
        conn = pool.acquire()
        try:
            conn.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER)")
            conn.execute("INSERT INTO test (id) VALUES (?)", (1,))
            conn.commit()
            
            cursor = conn.execute("SELECT id FROM test")
            result = cursor.fetchone()
            assert result[0] == 1
        finally:
            pool.release(conn)

    def test_context_manager(self, pool):
        """Test using pool with context manager."""
        with pool.get_connection() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS test2 (value TEXT)")
            conn.execute("INSERT INTO test2 (value) VALUES (?)", ("hello",))
            conn.commit()

    def test_multiple_connections(self, pool):
        """Test acquiring multiple connections."""
        connections = []
        for _ in range(3):
            conn = pool.acquire()
            connections.append(conn)
        
        assert len(connections) == 3
        
        for conn in connections:
            pool.release(conn)

    def test_pool_stats(self, pool):
        """Test that pool statistics are tracked."""
        conn = pool.acquire()
        stats = pool.get_stats()
        
        assert stats["total_connections"] >= 1
        assert stats["active_connections"] == 1
        assert "database_path" in stats
        assert stats["is_closed"] is False
        
        pool.release(conn)
        
        stats = pool.get_stats()
        assert stats["active_connections"] == 0

    def test_initial_min_connections(self, tmp_path):
        """Test that pool creates minimum connections on init."""
        db_path = str(tmp_path / "test_min.db")
        config = PoolConfig(min_connections=3, max_connections=10)
        pool = ConnectionPool(db_path, config)
        
        try:
            stats = pool.get_stats()
            assert stats["total_connections"] >= 3
        finally:
            pool.close()

    def test_thread_safety(self, pool):
        """Test that pool operations are thread-safe."""
        errors = []
        results = []

        def worker(worker_id):
            try:
                for _ in range(5):
                    conn = pool.acquire()
                    time.sleep(0.01)
                    pool.release(conn)
                    results.append(worker_id)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 25  # 5 threads * 5 iterations

    def test_close_pool(self, tmp_path):
        """Test closing the pool."""
        db_path = str(tmp_path / "test_close.db")
        pool = ConnectionPool(db_path)
        
        conn = pool.acquire()
        pool.release(conn)
        pool.close()
        
        assert pool.get_stats()["is_closed"] is True

    def test_connection_rollback_on_error(self, pool):
        """Test that connection rolls back on error."""
        with pytest.raises(Exception):
            with pool.get_connection() as conn:
                conn.execute("CREATE TABLE IF NOT EXISTS rollback_test (id INTEGER)")
                conn.execute("INSERT INTO rollback_test (id) VALUES (?)", (1,))
                raise Exception("Simulated error")
        
        # Verify the transaction was rolled back
        with pool.get_connection() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS rollback_test (id INTEGER)")
            cursor = conn.execute("SELECT COUNT(*) FROM rollback_test")
            count = cursor.fetchone()[0]
            # Table might not exist or be empty due to rollback
            assert count == 0


class TestGlobalPoolRegistry:
    """Test the global connection pool registry."""

    def test_get_same_pool_for_same_path(self, tmp_path):
        """Test that get_connection_pool returns same instance for same path."""
        db_path = str(tmp_path / "shared.db")
        
        pool1 = get_connection_pool(db_path)
        pool2 = get_connection_pool(db_path)
        
        assert pool1 is pool2
        
        # Cleanup
        close_all_pools()

    def test_different_paths_different_pools(self, tmp_path):
        """Test that different paths get different pools."""
        path1 = str(tmp_path / "db1.db")
        path2 = str(tmp_path / "db2.db")
        
        pool1 = get_connection_pool(path1)
        pool2 = get_connection_pool(path2)
        
        assert pool1 is not pool2
        
        # Cleanup
        close_all_pools()
