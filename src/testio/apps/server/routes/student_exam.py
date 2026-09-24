"""FastAPI route for the student exam page."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from testio.apps.server.database.exam_sessions import ExamSessionsTable
from testio.apps.server.validation import ValidationError, validate_session_id

student_exam_router = APIRouter()


@student_exam_router.get("/student/{session_id}", response_class=HTMLResponse)
def student_exam_page(request: Request, session_id: str) -> HTMLResponse:
    """Renders the student exam page for a specific session.

    Only the number of tests is passed to the template - never the config,
    whose expected outputs are the exam's answers.

    :param request: The FastAPI request object
    :param session_id: The exam session ID
    :return: The rendered HTML for the student exam page
    """
    try:
        session_id = validate_session_id(session_id)
    except ValidationError:
        raise HTTPException(status_code=404, detail="Exam session not found")

    exam_db = ExamSessionsTable()
    try:
        session = exam_db.get_session(session_id)
    finally:
        exam_db.close()

    if not session:
        raise HTTPException(status_code=404, detail="Exam session not found")

    if not session["is_active"]:
        raise HTTPException(
            status_code=403, detail="This exam session is no longer active"
        )

    tests = session["config_data"].get("tests") or []
    templates = request.app.state.templates
    mode = getattr(request.app.state, "mode", "teacher")
    return templates.TemplateResponse(
        request,
        "student_exam.html",
        {
            "session_id": session_id,
            "total_tests": len(tests) if isinstance(tests, list) else 0,
            "mode": mode,
        },
    )
