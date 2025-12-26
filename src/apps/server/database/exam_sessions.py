"""Database management for exam sessions and student submissions."""
import sys
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

sys.path.append(".")

from src.apps.server.database.database import Database


class ExamSessionsTable:
    """Manages exam sessions in the database."""

    def __init__(self, db_path: str = "testio.db"):
        """Initialize the exam sessions table.
        
        :param db_path: Path to the SQLite database file
        """
        self.db = Database.get_instance(db_path)
        self.db.__enter__()
        
        # Create exam_sessions table
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS exam_sessions (
                session_id TEXT PRIMARY KEY,
                config_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
            """
        )
        
        # Create student_submissions table
        self.db.execute(
            """
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
            """
        )

    def create_session(self, session_id: str, config_data: Dict[str, Any]) -> bool:
        """Create a new exam session.
        
        :param session_id: Unique identifier for the session
        :param config_data: Test configuration data
        :return: True if successful, False otherwise
        """
        try:
            self.db.execute(
                """
                INSERT INTO exam_sessions (session_id, config_data, created_at)
                VALUES (?, ?, ?)
                """,
                (session_id, json.dumps(config_data), datetime.now().isoformat())
            )
            return True
        except Exception as e:
            print(f"Error creating session: {e}")
            return False

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an exam session by ID.
        
        :param session_id: The session ID to retrieve
        :return: Session data or None if not found
        """
        self.db.execute(
            """
            SELECT session_id, config_data, created_at, is_active
            FROM exam_sessions
            WHERE session_id = ?
            """,
            (session_id,)
        )
        
        result = self.db.cursor.fetchone()
        if result:
            return {
                "session_id": result[0],
                "config_data": json.loads(result[1]),
                "created_at": result[2],
                "is_active": bool(result[3])
            }
        return None

    def end_session(self, session_id: str) -> bool:
        """Mark a session as inactive.
        
        :param session_id: The session ID to end
        :return: True if successful, False otherwise
        """
        try:
            self.db.execute(
                """
                UPDATE exam_sessions
                SET is_active = 0
                WHERE session_id = ?
                """,
                (session_id,)
            )
            return True
        except Exception as e:
            print(f"Error ending session: {e}")
            return False

    def submit_student_work(
        self, 
        session_id: str, 
        student_id: str, 
        student_code: str,
        test_results: Optional[List[Dict[str, Any]]] = None,
        score: Optional[float] = None
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
            self.db.execute(
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
                    datetime.now().isoformat()
                )
            )
            return True
        except Exception as e:
            print(f"Error submitting work: {e}")
            return False

    def get_session_submissions(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all submissions for a session.
        
        :param session_id: The exam session ID
        :return: List of submission data
        """
        self.db.execute(
            """
            SELECT student_id, student_code, test_results, score, submitted_at
            FROM student_submissions
            WHERE session_id = ?
            ORDER BY submitted_at DESC
            """,
            (session_id,)
        )
        
        results = self.db.cursor.fetchall()
        submissions = []
        for row in results:
            submissions.append({
                "student_id": row[0],
                "student_code": row[1],
                "test_results": json.loads(row[2]) if row[2] else None,
                "score": row[3],
                "submitted_at": row[4]
            })
        return submissions

    def get_student_submission(
        self, 
        session_id: str, 
        student_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific student's submission.
        
        :param session_id: The exam session ID
        :param student_id: The student ID
        :return: Submission data or None
        """
        self.db.execute(
            """
            SELECT student_code, test_results, score, submitted_at
            FROM student_submissions
            WHERE session_id = ? AND student_id = ?
            """,
            (session_id, student_id)
        )
        
        result = self.db.cursor.fetchone()
        if result:
            return {
                "student_code": result[0],
                "test_results": json.loads(result[1]) if result[1] else None,
                "score": result[2],
                "submitted_at": result[3]
            }
        return None

    def close(self):
        """Close the database connection."""
        self.db.__exit__(None, None, None)
