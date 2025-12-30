"""This module defines FastAPI routes for statistics and analytics."""
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

sys.path.append(".")

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.apps.server.database.exam_sessions import ExamSessionsTable

stats_router: APIRouter = APIRouter(tags=["Statistics"])


class SessionStats(BaseModel):
    """Statistics for a single exam session."""
    session_id: str
    total_submissions: int
    average_score: float
    highest_score: float
    lowest_score: float
    pass_rate: float
    created_at: str
    is_active: bool


class OverallStats(BaseModel):
    """Overall system statistics."""
    total_sessions: int
    total_submissions: int
    active_sessions: int
    average_score: float
    timestamp: str


class LeaderboardEntry(BaseModel):
    """A single leaderboard entry."""
    rank: int
    student_id: str
    score: float
    submitted_at: str


class LeaderboardResponse(BaseModel):
    """Response model for leaderboard endpoint."""
    session_id: str
    entries: List[LeaderboardEntry]
    total_entries: int


@stats_router.get("/api/stats/session/{session_id}", response_model=SessionStats)
async def get_session_stats(session_id: str) -> SessionStats:
    """
    Get statistics for a specific exam session.
    
    :param session_id: The session ID
    :return: Session statistics
    """
    exam_db = ExamSessionsTable()
    try:
        session = exam_db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        submissions = exam_db.get_session_submissions(session_id)
        
        if not submissions:
            return SessionStats(
                session_id=session_id,
                total_submissions=0,
                average_score=0.0,
                highest_score=0.0,
                lowest_score=0.0,
                pass_rate=0.0,
                created_at=session["created_at"],
                is_active=session["is_active"]
            )
        
        scores = [s["score"] for s in submissions if s["score"] is not None]
        passing_threshold = 60.0
        passing_count = len([s for s in scores if s >= passing_threshold])
        
        return SessionStats(
            session_id=session_id,
            total_submissions=len(submissions),
            average_score=round(sum(scores) / len(scores), 2) if scores else 0.0,
            highest_score=max(scores) if scores else 0.0,
            lowest_score=min(scores) if scores else 0.0,
            pass_rate=round((passing_count / len(scores)) * 100, 2) if scores else 0.0,
            created_at=session["created_at"],
            is_active=session["is_active"]
        )
    finally:
        exam_db.close()


@stats_router.get("/api/stats/leaderboard/{session_id}", response_model=LeaderboardResponse)
async def get_session_leaderboard(
    session_id: str, 
    limit: int = 10
) -> LeaderboardResponse:
    """
    Get the leaderboard for a specific exam session.
    
    :param session_id: The session ID
    :param limit: Maximum number of entries to return (default: 10)
    :return: Leaderboard with ranked entries
    """
    exam_db = ExamSessionsTable()
    try:
        session = exam_db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        submissions = exam_db.get_session_submissions(session_id)
        
        # Sort by score (descending) and submitted_at (ascending for ties)
        sorted_submissions = sorted(
            submissions,
            key=lambda x: (-(x["score"] or 0), x["submitted_at"])
        )
        
        # Limit results
        limited_submissions = sorted_submissions[:limit]
        
        entries = [
            LeaderboardEntry(
                rank=i + 1,
                student_id=sub["student_id"],
                score=sub["score"] or 0.0,
                submitted_at=sub["submitted_at"]
            )
            for i, sub in enumerate(limited_submissions)
        ]
        
        return LeaderboardResponse(
            session_id=session_id,
            entries=entries,
            total_entries=len(submissions)
        )
    finally:
        exam_db.close()
