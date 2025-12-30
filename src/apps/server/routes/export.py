"""This module defines FastAPI routes for exporting test results and submissions."""
import sys
import csv
import io
from datetime import datetime
from typing import Dict, Any, List

sys.path.append(".")

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.apps.server.database.exam_sessions import ExamSessionsTable

export_router: APIRouter = APIRouter(tags=["Export"])


class ExportFormat:
    """Supported export formats."""
    CSV = "csv"
    JSON = "json"


@export_router.get("/api/export/session/{session_id}")
async def export_session_results(
    session_id: str,
    format: str = "json"
) -> Any:
    """
    Export all submission results for an exam session.
    
    :param session_id: The session ID
    :param format: Export format ('json' or 'csv')
    :return: Exported data in the specified format
    """
    exam_db = ExamSessionsTable()
    try:
        session = exam_db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        submissions = exam_db.get_session_submissions(session_id)
        
        if format.lower() == ExportFormat.CSV:
            return _export_as_csv(session_id, submissions)
        else:
            return _export_as_json(session_id, session, submissions)
    finally:
        exam_db.close()


def _export_as_json(
    session_id: str,
    session: Dict[str, Any],
    submissions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Export submissions as JSON.
    
    :param session_id: The session ID
    :param session: Session data
    :param submissions: List of submissions
    :return: JSON formatted data
    """
    # Calculate summary statistics
    scores = [s["score"] for s in submissions if s["score"] is not None]
    
    return {
        "session_id": session_id,
        "exported_at": datetime.now().isoformat(),
        "session_info": {
            "created_at": session["created_at"],
            "is_active": session["is_active"]
        },
        "summary": {
            "total_submissions": len(submissions),
            "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "highest_score": max(scores) if scores else 0,
            "lowest_score": min(scores) if scores else 0
        },
        "submissions": [
            {
                "student_id": sub["student_id"],
                "score": sub["score"],
                "submitted_at": sub["submitted_at"],
                "test_summary": _summarize_test_results(sub.get("test_results"))
            }
            for sub in submissions
        ]
    }


def _summarize_test_results(test_results: List[Dict] | None) -> Dict[str, int]:
    """
    Summarize test results into counts.
    
    :param test_results: List of test results
    :return: Summary dictionary with counts
    """
    if not test_results:
        return {"total": 0, "passed": 0, "failed": 0}
    
    total = len(test_results)
    passed = sum(1 for r in test_results if r.get("result") == "ComparisonResult.MATCH")
    
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed
    }


def _export_as_csv(session_id: str, submissions: List[Dict[str, Any]]) -> StreamingResponse:
    """
    Export submissions as CSV.
    
    :param session_id: The session ID
    :param submissions: List of submissions
    :return: Streaming CSV response
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Student ID",
        "Score",
        "Submitted At",
        "Total Tests",
        "Passed Tests",
        "Failed Tests"
    ])
    
    # Write data rows
    for sub in submissions:
        test_summary = _summarize_test_results(sub.get("test_results"))
        writer.writerow([
            sub["student_id"],
            sub["score"],
            sub["submitted_at"],
            test_summary["total"],
            test_summary["passed"],
            test_summary["failed"]
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=session_{session_id}_results.csv"
        }
    )


@export_router.get("/api/export/student/{session_id}/{student_id}")
async def export_student_submission(
    session_id: str,
    student_id: str
) -> Dict[str, Any]:
    """
    Export a specific student's submission details.
    
    :param session_id: The session ID
    :param student_id: The student ID
    :return: Student's submission data
    """
    exam_db = ExamSessionsTable()
    try:
        session = exam_db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        submission = exam_db.get_student_submission(session_id, student_id)
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        return {
            "session_id": session_id,
            "student_id": student_id,
            "exported_at": datetime.now().isoformat(),
            "score": submission["score"],
            "submitted_at": submission["submitted_at"],
            "code": submission["student_code"],
            "test_results": submission["test_results"]
        }
    finally:
        exam_db.close()
