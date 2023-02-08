import sys
from dataclasses import asdict

sys.path.append(".")

import sqlite3
from typing import Dict, List, Optional

from src.core.execution.data import ExecutionManagerInputData


class Database:
    """A class to handle custom database interactions for an SQLite database."""

    _instance = None

    def __init__(self, database_file: str):
        """
        Initialize the database connection.

        :param database_file: The file path of the SQLite database.
        """
        if Database._instance is not None:
            raise Exception(
                "Database is a singleton class and cannot be instantiated directly"
            )

        self.database_file = database_file
        self.conn = None
        self.cursor = None

    def __enter__(self):
        """Enter the context manager and establish a database connection."""
        self.conn = sqlite3.connect(self.database_file)
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Exit the context manager and commit and close the database connection."""
        self.conn.commit()
        self.conn.close()

    def execute(self, sql: str, params: Optional[tuple] = None):
        """
        Execute an SQL command.

        :param sql: The SQL command to be executed.
        :param params: A tuple of parameters to replace placeholders in the SQL command.
        """
        if params:
            self.cursor.execute(sql, params)
        else:
            self.cursor.execute(sql)

    @staticmethod
    def get_instance(database_file: str) -> "Database":
        """
        Get the single instance of the `Database` class.

        :param database_file: The file path of the SQLite database.
        :return: The single instance of the `Database` class.
        """
        if Database._instance is None:
            Database._instance = Database(database_file)
        return Database._instance


import json


class ExecutionManagerDataTable:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute(
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

            self.cursor.execute(
                """
                INSERT OR REPLACE INTO test_data (filename, data)
                VALUES (?, ?)
            """,
                (filename, serialized_data),
            )

        self.conn.commit()

    def retrieve_table(self) -> Optional[Dict[str, List[ExecutionManagerInputData]]]:
        """
        Retrieve all the test data.

        :return: A dictionary where filenames are keys and values are lists of `ExecutionManagerInputData` objects, or None if no data is found.
        """
        self.cursor.execute(
            """
            SELECT filename, data
            FROM test_data
        """
        )

        result = self.cursor.fetchall()
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
        self.cursor.execute(
            """
            SELECT data
            FROM test_data
            WHERE filename = ?
        """,
            (filename,),
        )

        result = self.cursor.fetchone()
        if result:
            # Deserialize the test data from a string
            serialized_data = result[0]
            test_data = json.loads(serialized_data)
            return [ExecutionManagerInputData(**input_data) for input_data in test_data]
        else:
            return None

    def close(self):
        self.conn.close()
