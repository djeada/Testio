"""
Connection pool for SQLite database connections.
Provides thread-safe connection pooling with configurable limits.
"""

import sqlite3
import threading
import time
import logging
from queue import Queue, Empty
from dataclasses import dataclass
from typing import Any, Dict, Iterator, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class PoolConfig:
    """Configuration for the connection pool."""
    min_connections: int = 2
    max_connections: int = 10
    connection_timeout: float = 30.0
    idle_timeout: float = 300.0
    check_same_thread: bool = False


class PooledConnection:
    """
    A wrapper around a SQLite connection that tracks metadata.
    """

    def __init__(
        self, 
        connection: sqlite3.Connection,
        pool: "ConnectionPool"
    ):
        """
        Initialize a pooled connection.

        :param connection: The underlying SQLite connection
        :param pool: Reference to the parent pool
        """
        self._connection = connection
        self._pool = pool
        self._created_at = time.time()
        self._last_used = time.time()
        self._in_use = False
        self._use_count = 0

    @property
    def connection(self) -> sqlite3.Connection:
        """Get the underlying connection."""
        return self._connection

    @property
    def cursor(self) -> sqlite3.Cursor:
        """Get a cursor from the connection."""
        return self._connection.cursor()

    @property
    def is_stale(self) -> bool:
        """Check if the connection has been idle too long."""
        return (
            time.time() - self._last_used > self._pool.config.idle_timeout
        )

    def execute(self, sql: str, params: Optional[tuple] = None) -> sqlite3.Cursor:
        """
        Execute an SQL statement.

        :param sql: SQL statement
        :param params: Optional parameters
        :return: Cursor with results
        """
        cursor = self._connection.cursor()
        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor
        except sqlite3.Error as e:
            logger.error(f"SQL execution error: {e}")
            raise

    def executemany(
        self, 
        sql: str, 
        params_list: list
    ) -> sqlite3.Cursor:
        """
        Execute SQL statement with multiple parameter sets.

        :param sql: SQL statement
        :param params_list: List of parameter tuples
        :return: Cursor with results
        """
        cursor = self._connection.cursor()
        cursor.executemany(sql, params_list)
        return cursor

    def commit(self) -> None:
        """Commit the current transaction."""
        self._connection.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self._connection.rollback()

    def mark_used(self) -> None:
        """Mark the connection as used."""
        self._last_used = time.time()
        self._use_count += 1
        self._in_use = True

    def mark_released(self) -> None:
        """Mark the connection as released."""
        self._in_use = False
        self._last_used = time.time()

    def close(self) -> None:
        """Close the underlying connection."""
        try:
            self._connection.close()
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")


class ConnectionPool:
    """
    Thread-safe connection pool for SQLite databases.
    Manages a pool of reusable database connections.
    """

    def __init__(
        self,
        database_path: str,
        config: Optional[PoolConfig] = None
    ):
        """
        Initialize the connection pool.

        :param database_path: Path to the SQLite database
        :param config: Pool configuration
        """
        self.database_path = database_path
        self.config = config or PoolConfig()
        
        self._available: Queue[PooledConnection] = Queue()
        self._all_connections: list[PooledConnection] = []
        self._lock = threading.RLock()
        self._closed = False

        # Statistics
        self._total_connections_created = 0
        self._total_connections_closed = 0
        self._peak_connections = 0
        self._wait_count = 0
        self._total_wait_time = 0.0

        # Initialize minimum connections
        self._initialize_pool()

    def _initialize_pool(self) -> None:
        """Create the initial pool of connections."""
        for _ in range(self.config.min_connections):
            conn = self._create_connection()
            if conn:
                self._available.put(conn)

    def _create_connection(self) -> Optional[PooledConnection]:
        """
        Create a new database connection.

        :return: PooledConnection or None if failed
        """
        try:
            connection = sqlite3.connect(
                self.database_path,
                check_same_thread=self.config.check_same_thread
            )
            # Enable foreign keys
            connection.execute("PRAGMA foreign_keys = ON")
            # Optimize for performance
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = NORMAL")
            
            pooled = PooledConnection(connection, self)
            
            with self._lock:
                self._all_connections.append(pooled)
                self._total_connections_created += 1
                current_count = len(self._all_connections)
                self._peak_connections = max(
                    self._peak_connections, current_count
                )
            
            logger.debug(
                f"Created new connection (total: {current_count})"
            )
            return pooled

        except sqlite3.Error as e:
            logger.error(f"Failed to create connection: {e}")
            return None

    @contextmanager
    def get_connection(self) -> Iterator[PooledConnection]:
        """
        Get a connection from the pool.
        Automatically returns the connection when done.

        :yield: PooledConnection
        """
        connection = self.acquire()
        try:
            yield connection
        except Exception:
            connection.rollback()
            raise
        finally:
            self.release(connection)

    def acquire(self) -> PooledConnection:
        """
        Acquire a connection from the pool.

        :return: A PooledConnection
        :raises RuntimeError: If pool is closed or timeout exceeded
        """
        if self._closed:
            raise RuntimeError("Connection pool is closed")

        start_time = time.time()

        # Try to get an available connection
        while True:
            try:
                connection = self._available.get_nowait()
                
                # Check if connection is stale
                if connection.is_stale:
                    self._remove_connection(connection)
                    continue
                
                connection.mark_used()
                return connection

            except Empty:
                pass

            # Check if we can create a new connection
            with self._lock:
                current_count = len(self._all_connections)
                if current_count < self.config.max_connections:
                    connection = self._create_connection()
                    if connection:
                        connection.mark_used()
                        return connection

            # Wait for a connection to become available
            elapsed = time.time() - start_time
            if elapsed >= self.config.connection_timeout:
                raise RuntimeError(
                    f"Connection timeout after {elapsed:.1f}s"
                )

            with self._lock:
                self._wait_count += 1

            try:
                connection = self._available.get(
                    timeout=min(1.0, self.config.connection_timeout - elapsed)
                )
                with self._lock:
                    self._total_wait_time += time.time() - start_time

                if connection.is_stale:
                    self._remove_connection(connection)
                    continue

                connection.mark_used()
                return connection

            except Empty:
                continue

    def release(self, connection: PooledConnection) -> None:
        """
        Return a connection to the pool.

        :param connection: The connection to release
        """
        if self._closed:
            connection.close()
            return

        connection.commit()
        connection.mark_released()
        self._available.put(connection)
        logger.debug("Connection released to pool")

    def _remove_connection(self, connection: PooledConnection) -> None:
        """
        Remove a connection from the pool.

        :param connection: The connection to remove
        """
        with self._lock:
            try:
                self._all_connections.remove(connection)
                self._total_connections_closed += 1
            except ValueError:
                pass
        connection.close()
        logger.debug("Stale connection removed from pool")

    def close(self) -> None:
        """Close all connections and shut down the pool."""
        self._closed = True
        
        # Close all available connections
        while True:
            try:
                conn = self._available.get_nowait()
                conn.close()
            except Empty:
                break

        # Close any remaining connections
        with self._lock:
            for conn in self._all_connections:
                conn.close()
            self._all_connections.clear()

        logger.info("Connection pool closed")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get pool statistics.

        :return: Dictionary with pool statistics
        """
        with self._lock:
            active_count = sum(
                1 for c in self._all_connections if c._in_use
            )
            avg_wait = (
                self._total_wait_time / self._wait_count 
                if self._wait_count > 0 else 0.0
            )
            
            return {
                "database_path": self.database_path,
                "total_connections": len(self._all_connections),
                "available_connections": self._available.qsize(),
                "active_connections": active_count,
                "min_connections": self.config.min_connections,
                "max_connections": self.config.max_connections,
                "peak_connections": self._peak_connections,
                "total_created": self._total_connections_created,
                "total_closed": self._total_connections_closed,
                "wait_count": self._wait_count,
                "avg_wait_ms": round(avg_wait * 1000, 2),
                "is_closed": self._closed
            }


# Global connection pool registry
_pools: Dict[str, ConnectionPool] = {}
_pools_lock = threading.Lock()


def get_connection_pool(
    database_path: str,
    config: Optional[PoolConfig] = None
) -> ConnectionPool:
    """
    Get or create a connection pool for the given database.

    :param database_path: Path to the SQLite database
    :param config: Optional pool configuration
    :return: ConnectionPool instance
    """
    with _pools_lock:
        if database_path not in _pools:
            _pools[database_path] = ConnectionPool(database_path, config)
        return _pools[database_path]


def close_all_pools() -> None:
    """Close all connection pools."""
    with _pools_lock:
        for pool in _pools.values():
            pool.close()
        _pools.clear()
