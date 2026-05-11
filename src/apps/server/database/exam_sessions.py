"""Database management for exam sessions, student exam submissions, and exercise submissions."""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from src.apps.server.database.connection_pool import get_connection_pool
from src.apps.server.settings import get_app_database_path
from src.core.caching.memory_cache import cache_result

logger = logging.getLogger(__name__)


class ExamSessionsTable:
    """Manages exam sessions in the database."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the exam sessions table.

        :param db_path: Path to the SQLite database file
        """
        self.db_path = db_path or get_app_database_path()
        self.pool = get_connection_pool(self.db_path)

    def _ensure_tables(self) -> None:
        # Create exam_sessions table
        with self.pool.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS exam_sessions (
                    session_id TEXT PRIMARY KEY,
                    config_data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    closed_at TEXT,
                    is_active INTEGER DEFAULT 1,
                    is_deleted INTEGER DEFAULT 0
                )
                """)

            # Create student_submissions table (exam mode)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS student_submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    student_id TEXT NOT NULL,
                    student_code TEXT NOT NULL,
                    test_results TEXT,
                    score REAL,
                    submitted_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES exam_sessions(session_id),
                    UNIQUE(session_id, student_id)
                )
                """)

            # Create exercise_submissions table (self-service / teacher-review mode)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS exercise_submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_name TEXT NOT NULL,
                    problem_description TEXT,
                    code TEXT NOT NULL,
                    additional_files TEXT,
                    test_results TEXT,
                    score REAL,
                    submitted_at TEXT NOT NULL
                )
                """)

            # Idempotent column migrations
            for migration in [
                "ALTER TABLE exam_sessions ADD COLUMN closed_at TEXT",
                "ALTER TABLE exam_sessions ADD COLUMN is_deleted INTEGER DEFAULT 0",
            ]:
                try:
                    conn.execute(migration)
                    conn.commit()
                except Exception:
                    pass

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_student_submissions_session_id
                ON student_submissions(session_id)
                """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_student_submissions_submitted_at
                ON student_submissions(submitted_at)
                """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_exam_sessions_is_active
                ON exam_sessions(is_active)
                """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_exam_sessions_is_deleted
                ON exam_sessions(is_deleted)
                """)
            conn.commit()

    def create_session(self, session_id: str, config_data: Dict[str, Any]) -> bool:
        """Create a new exam session.

        :param session_id: Unique identifier for the session
        :param config_data: Test configuration data
        :return: True if successful, False otherwise
        """
        try:
            self._ensure_tables()
            with self.pool.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO exam_sessions (session_id, config_data, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (session_id, json.dumps(config_data), datetime.now().isoformat()),
                )
            return True
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return False

    @cache_result(ttl=15.0, key_prefix="exam_session")
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an exam session by ID.

        Results are cached for 15 seconds to reduce DB load on heavily polled
        endpoints. The cache is keyed on (self, session_id) so each session ID
        gets its own entry. Short TTL ensures stale data is never served for
        long.

        :param session_id: The session ID to retrieve
        :return: Session data or None if not found
        """
        self._ensure_tables()
        with self.pool.get_connection() as conn:
            result = conn.execute(
                """
                SELECT session_id, config_data, created_at, is_active, closed_at
                FROM exam_sessions
                WHERE session_id = ? AND is_deleted = 0
                """,
                (session_id,),
            ).fetchone()
        if result:
            return {
                "session_id": result[0],
                "config_data": json.loads(result[1]),
                "created_at": result[2],
                "is_active": bool(result[3]),
                "closed_at": result[4],
            }
        return None

    def end_session(self, session_id: str) -> bool:
        """Mark a session as inactive.

        :param session_id: The session ID to end
        :return: True if successful, False otherwise
        """
        try:
            self._ensure_tables()
            with self.pool.get_connection() as conn:
                conn.execute(
                    """
                    UPDATE exam_sessions
                    SET is_active = 0, closed_at = ?
                    WHERE session_id = ?
                    """,
                    (datetime.now().isoformat(), session_id),
                )
            return True
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return False

    def submit_student_work(
        self,
        session_id: str,
        student_id: str,
        student_code: str,
        test_results: Optional[List[Dict[str, Any]]] = None,
        score: Optional[float] = None,
    ) -> bool:
        """Submit or update a student's work for an exam session.

        :param session_id: The exam session ID
        :param student_id: Student identifier
        :param student_code: The student's code submission
        :param test_results: Test results data (optional)
        :param score: Student's score (optional)
        :return: True if successful, False otherwise
        """
        try:
            self._ensure_tables()
            with self.pool.get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO student_submissions
                    (session_id, student_id, student_code, test_results, score, submitted_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        student_id,
                        student_code,
                        json.dumps(test_results) if test_results else None,
                        score,
                        datetime.now().isoformat(),
                    ),
                )
            return True
        except Exception as e:
            logger.error(f"Error submitting work: {e}")
            return False

    def get_session_submissions(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all submissions for a session.

        :param session_id: The exam session ID
        :return: List of submission data
        """
        self._ensure_tables()
        with self.pool.get_connection() as conn:
            results = conn.execute(
                """
                SELECT student_id, student_code, test_results, score, submitted_at
                FROM student_submissions
                WHERE session_id = ?
                ORDER BY submitted_at DESC
                """,
                (session_id,),
            ).fetchall()
        submissions = []
        for row in results:
            submissions.append(
                {
                    "student_id": row[0],
                    "student_code": row[1],
                    "test_results": json.loads(row[2]) if row[2] else None,
                    "score": row[3],
                    "submitted_at": row[4],
                }
            )
        return submissions

    def get_student_submission(
        self, session_id: str, student_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific student's submission.

        :param session_id: The exam session ID
        :param student_id: The student ID
        :return: Submission data or None
        """
        self._ensure_tables()
        with self.pool.get_connection() as conn:
            result = conn.execute(
                """
                SELECT student_code, test_results, score, submitted_at
                FROM student_submissions
                WHERE session_id = ? AND student_id = ?
                """,
                (session_id, student_id),
            ).fetchone()
        if result:
            return {
                "student_code": result[0],
                "test_results": json.loads(result[1]) if result[1] else None,
                "score": result[2],
                "submitted_at": result[3],
            }
        return None

    def close(self):
        """Compatibility no-op; pooled connections are scoped per operation."""
        logger.debug(
            "ExamSessionsTable.close() called; pooled connections remain managed by the pool"
        )

    # ------------------------------------------------------------------
    # Soft-delete / listing for exam sessions
    # ------------------------------------------------------------------

    def delete_session(self, session_id: str) -> bool:
        """Soft-delete an exam session (GDPR-style cleanup).

        :param session_id: The session ID to delete
        :return: True if the session was found and marked deleted
        """
        try:
            self._ensure_tables()
            with self.pool.get_connection() as conn:
                cursor = conn.execute(
                    "UPDATE exam_sessions SET is_deleted = 1 WHERE session_id = ? AND is_deleted = 0",
                    (session_id,),
                )
                conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False

    def get_all_sessions(self, include_inactive: bool = True) -> List[Dict[str, Any]]:
        """Return all non-deleted exam sessions.

        :param include_inactive: When False, only active sessions are returned.
        :return: List of session data dicts.
        """
        self._ensure_tables()
        query = """
            SELECT session_id, config_data, created_at, is_active, closed_at
            FROM exam_sessions
            WHERE is_deleted = 0
        """
        if not include_inactive:
            query += " AND is_active = 1"
        query += " ORDER BY created_at DESC"

        with self.pool.get_connection() as conn:
            results = conn.execute(query).fetchall()

        sessions = []
        for row in results:
            sessions.append(
                {
                    "session_id": row[0],
                    "config_data": json.loads(row[1]),
                    "created_at": row[2],
                    "is_active": bool(row[3]),
                    "closed_at": row[4],
                }
            )
        return sessions

    # ------------------------------------------------------------------
    # Exercise submissions (non-exam self-service flow)
    # ------------------------------------------------------------------

    def store_exercise_submission(
        self,
        student_name: str,
        problem_description: Optional[str],
        code: str,
        additional_files: Optional[List[Dict[str, Any]]] = None,
        test_results: Optional[List[Dict[str, Any]]] = None,
        score: Optional[float] = None,
    ) -> Optional[int]:
        """Persist a student exercise submission.

        :return: Auto-increment row ID, or None on failure.
        """
        try:
            self._ensure_tables()
            with self.pool.get_connection() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO exercise_submissions
                    (student_name, problem_description, code, additional_files,
                     test_results, score, submitted_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        student_name,
                        problem_description,
                        code,
                        json.dumps(additional_files) if additional_files else None,
                        json.dumps(test_results) if test_results else None,
                        score,
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error storing exercise submission: {e}")
            return None

    def get_exercise_submissions(
        self, page: int = 1, page_size: int = 20
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """Return paginated exercise submissions.

        :return: (total_count, list of submission dicts)
        """
        self._ensure_tables()
        offset = (page - 1) * page_size
        with self.pool.get_connection() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM exercise_submissions"
            ).fetchone()[0]
            rows = conn.execute(
                """
                SELECT id, student_name, problem_description, code,
                       additional_files, test_results, score, submitted_at
                FROM exercise_submissions
                ORDER BY submitted_at DESC
                LIMIT ? OFFSET ?
                """,
                (page_size, offset),
            ).fetchall()

        submissions = []
        for row in rows:
            submissions.append(
                {
                    "id": row[0],
                    "student_name": row[1],
                    "problem_description": row[2],
                    "code": row[3],
                    "additional_files": json.loads(row[4]) if row[4] else [],
                    "test_results": json.loads(row[5]) if row[5] else None,
                    "score": row[6],
                    "submitted_at": row[7],
                }
            )
        return total, submissions

    def get_exercise_submission_by_id(
        self, submission_id: int
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a single exercise submission by ID."""
        self._ensure_tables()
        with self.pool.get_connection() as conn:
            row = conn.execute(
                """
                SELECT id, student_name, problem_description, code,
                       additional_files, test_results, score, submitted_at
                FROM exercise_submissions
                WHERE id = ?
                """,
                (submission_id,),
            ).fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "student_name": row[1],
            "problem_description": row[2],
            "code": row[3],
            "additional_files": json.loads(row[4]) if row[4] else [],
            "test_results": json.loads(row[5]) if row[5] else None,
            "score": row[6],
            "submitted_at": row[7],
        }
