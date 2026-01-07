"""FastAPI route for the student exam page."""
import sys

sys.path.append(".")

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse

from src.apps.server.database.exam_sessions import ExamSessionsTable

student_exam_router = APIRouter()


@student_exam_router.get("/student/{session_id}", response_class=HTMLResponse)
def student_exam_page(request: Request, session_id: str) -> HTMLResponse:
    """Renders the student exam page for a specific session.
    
    :param request: The FastAPI request object
    :param session_id: The exam session ID
    :return: The rendered HTML for the student exam page
    """
    # Verify the session exists
    exam_db = ExamSessionsTable()
    try:
        session = exam_db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Exam session not found")
        
        if not session["is_active"]:
            raise HTTPException(status_code=403, detail="This exam session is no longer active")
        
        templates = request.app.state.templates
        mode = getattr(request.app.state, 'mode', 'teacher')
        return templates.TemplateResponse(
            request, 
            "student_exam.html", 
            {
                "session_id": session_id,
                "config_data": session["config_data"],
                "mode": mode
            }
        )
    finally:
        exam_db.close()
