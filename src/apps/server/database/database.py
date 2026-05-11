"""Database table helpers backed by the shared SQLite connection pool."""

from dataclasses import asdict

import json
import logging
from typing import Dict, List, Optional

from src.apps.server.database.connection_pool import get_connection_pool
from src.core.execution.data import ExecutionManagerInputData

logger = logging.getLogger(__name__)


class ExecutionManagerDataTable:
    """Persistence helper for stored execution-manager configuration data."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.pool = get_connection_pool(db_path)
        self._ensure_table()

    def _ensure_table(self) -> None:
        with self.pool.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_data (
                    filename TEXT PRIMARY KEY,
                    data TEXT NOT NULL
                )
                """)

    def store_data(self, data: Dict[str, List[ExecutionManagerInputData]]) -> None:
        rows = []
        for filename, test_data in data.items():
            serialized_data = json.dumps(
                [asdict(input_data) for input_data in test_data]
            )
            rows.append((filename, serialized_data))

        if not rows:
            return

        with self.pool.get_connection() as conn:
            conn.execute("DELETE FROM test_data")
            conn.executemany(
                """
                INSERT OR REPLACE INTO test_data (filename, data)
                VALUES (?, ?)
                """,
                rows,
            )

    def retrieve_table(self) -> Optional[Dict[str, List[ExecutionManagerInputData]]]:
        """
        Retrieve all the test data.

        :return: A dictionary where filenames are keys and values are lists of
                 ExecutionManagerInputData objects, or None if no data is found.
        """
        with self.pool.get_connection() as conn:
            result = conn.execute("""
                SELECT filename, data
                FROM test_data
                """).fetchall()

        if not result:
            return None

        test_data_dict = {}
        for filename, serialized_data in result:
            test_data = json.loads(serialized_data)
            test_data_dict[filename] = [
                ExecutionManagerInputData(**input_data) for input_data in test_data
            ]
        return test_data_dict

    def retrieve_row(self, filename: str) -> Optional[List[ExecutionManagerInputData]]:
        """
        Retrieve test data for a given file.

        :param filename: The file name to retrieve test data for.
        :return: A list of ExecutionManagerInputData objects for the file, or None
                 if no data is found.
        """
        with self.pool.get_connection() as conn:
            result = conn.execute(
                """
                SELECT data
                FROM test_data
                WHERE filename = ?
                """,
                (filename,),
            ).fetchone()

        if not result:
            return None

        test_data = json.loads(result[0])
        return [ExecutionManagerInputData(**input_data) for input_data in test_data]

    def close(self) -> None:
        """Compatibility no-op; connections are returned to the shared pool per call."""
        logger.debug(
            "ExecutionManagerDataTable.close() called; pooled connections remain managed by the pool"
        )
