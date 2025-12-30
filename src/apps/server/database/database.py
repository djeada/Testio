import sys
from dataclasses import asdict
import threading

sys.path.append(".")

import sqlite3
from typing import Dict, List, Optional
import json
import logging

from src.core.execution.data import ExecutionManagerInputData

logger = logging.getLogger(__name__)


class Database:
    """A class to handle custom database interactions for an SQLite database.
    
    This class implements a thread-safe singleton pattern for database connections.
    Each instance is associated with a specific database file.
    """

    _instances: Dict[str, "Database"] = {}
    _lock = threading.Lock()

    def __init__(self, database_file: str):
        """
        Initialize the database connection.

        :param database_file: The file path of the SQLite database.
        """
        self.database_file = database_file
        self.conn = None
        self.cursor = None
        self._is_connected = False

    def __enter__(self):
        """Enter the context manager and establish a database connection.
        
        Note: check_same_thread=False is used because FastAPI handles requests
        in different threads. The singleton pattern with threading lock ensures
        only one Database instance exists. For high-concurrency scenarios,
        consider using a connection pool like SQLAlchemy.
        """
        if not self._is_connected:
            self.conn = sqlite3.connect(self.database_file, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self._is_connected = True
            logger.debug(f"Connected to database: {self.database_file}")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Exit the context manager and commit and close the database connection."""
        if self._is_connected and self.conn:
            self.conn.commit()
            self.conn.close()
            self._is_connected = False
            logger.debug(f"Disconnected from database: {self.database_file}")

    def execute(self, sql: str, params: Optional[tuple] = None):
        """
        Execute an SQL command.

        :param sql: The SQL command to be executed.
        :param params: A tuple of parameters to replace placeholders in the SQL command.
        """
        if not self._is_connected:
            raise RuntimeError("Database connection not established. Use context manager.")
        
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise

    def commit(self):
        """Commit the current transaction."""
        if self.conn:
            self.conn.commit()

    def is_connected(self) -> bool:
        """Check if the database is connected."""
        return self._is_connected

    @classmethod
    def get_instance(cls, database_file: str) -> "Database":
        """
        Get or create a Database instance for the specified file.
        Thread-safe singleton pattern.

        :param database_file: The file path of the SQLite database.
        :return: A Database instance for the specified file.
        """
        with cls._lock:
            if database_file not in cls._instances:
                cls._instances[database_file] = cls(database_file)
            return cls._instances[database_file]

    @classmethod
    def reset_instances(cls):
        """Reset all database instances. Useful for testing."""
        with cls._lock:
            for instance in cls._instances.values():
                if instance._is_connected:
                    instance.__exit__(None, None, None)
            cls._instances.clear()


class ExecutionManagerDataTable:
    def __init__(self, db_path):
        self.db = Database.get_instance(db_path)
        self.db.__enter__()

        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS test_data (
                filename TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
        """
        )

    def store_data(self, data):
        for filename, test_data in data.items():
            # Serialize the test data into a string
            serialized_data = json.dumps(
                [asdict(input_data) for input_data in test_data]
            )

            self.db.execute(
                """
                INSERT OR REPLACE INTO test_data (filename, data)
                VALUES (?, ?)
            """,
                (filename, serialized_data),
            )

    def retrieve_table(self) -> Optional[Dict[str, List[ExecutionManagerInputData]]]:
        """
        Retrieve all the test data.

        :return: A dictionary where filenames are keys and values are lists of `ExecutionManagerInputData` objects,
        or None if no data is found.
        """
        self.db.execute(
            """
            SELECT filename, data
            FROM test_data
        """
        )

        result = self.db.cursor.fetchall()
        if result:
            # Deserialize the test data from a string
            test_data_dict = {}
            for row in result:
                filename = row[0]
                serialized_data = row[1]
                test_data = json.loads(serialized_data)
                test_data_dict[filename] = [
                    ExecutionManagerInputData(**input_data) for input_data in test_data
                ]
            return test_data_dict
        else:
            return None

    def retrieve_row(self, filename: str) -> Optional[List[ExecutionManagerInputData]]:
        """
        Retrieve test data for a given file.

        :param filename: The file name to retrieve test data for.
        :return: A list of `ExecutionManagerInputData` objects for the file, or None if no data is found.
        """
        self.db.execute(
            """
            SELECT data
            FROM test_data
            WHERE filename = ?
        """,
            (filename,),
        )

        result = self.db.cursor.fetchone()
        if result:
            # Deserialize the test data from a string
            serialized_data = result[0]
            test_data = json.loads(serialized_data)
            return [ExecutionManagerInputData(**input_data) for input_data in test_data]
        else:
            return None

    def close(self):
        self.db.__exit__(None, None, None)
