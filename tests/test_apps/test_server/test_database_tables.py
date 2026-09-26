"""Tests for pooled database table helpers."""

import sys

sys.path.append(".")

from testio.apps.server.database.connection_pool import close_all_pools
from testio.apps.server.database.database import ExecutionManagerDataTable
from testio.apps.server.database.exam_sessions import ExamSessionsTable
from testio.core.execution.data import ExecutionManagerInputData


def test_execution_manager_data_table_round_trip(tmp_path):
    db_path = str(tmp_path / "config.db")
    table = ExecutionManagerDataTable(db_path)

    payload = {
        "prog.py": [
            ExecutionManagerInputData(
                command='python3 "prog.py"',
                input=["1"],
                output=["1"],
                timeout=5,
            )
        ]
    }

    table.store_data(payload)

    restored = table.retrieve_table()
    assert restored is not None
    assert restored["prog.py"][0].command == 'python3 "prog.py"'
    assert restored["prog.py"][0].input == ["1"]

    close_all_pools()


def test_exam_sessions_table_round_trip(tmp_path):
    db_path = str(tmp_path / "exam.db")
    table = ExamSessionsTable(db_path)

    assert table.create_session("session-1", {"tests": []}) is True
    assert (
        table.submit_student_work(
            "session-1",
            "student-1",
            "print(1)",
            [{"result_name": "MATCH", "result": "ComparisonResult.MATCH"}],
            100.0,
        )
        is True
    )

    session = table.get_session("session-1")
    submission = table.get_student_submission("session-1", "student-1")

    assert session is not None
    assert session["session_id"] == "session-1"
    assert submission is not None
    assert submission["score"] == 100.0
    assert submission["test_results"][0]["result_name"] == "MATCH"

    close_all_pools()


def test_old_database_is_migrated(tmp_path):
    """A database from an older version gains the new columns."""
    import sqlite3

    from testio.apps.server.database.exam_sessions import ExamSessionsTable

    db_path = str(tmp_path / "old.db")
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE exam_sessions (session_id TEXT PRIMARY KEY, "
            "config_data TEXT NOT NULL, created_at TEXT NOT NULL, "
            "is_active INTEGER DEFAULT 1)"
        )

    table = ExamSessionsTable(db_path)
    table._ensure_tables()
    table._ensure_tables()  # second call is a no-op

    with sqlite3.connect(db_path) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(exam_sessions)")}
    assert {"closed_at", "is_deleted"} <= columns
