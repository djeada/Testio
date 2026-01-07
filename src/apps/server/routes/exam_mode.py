"""This module defines a FastAPI router for the exam mode page."""
import sys

sys.path.append(".")
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

exam_mode_page_router = APIRouter()


@exam_mode_page_router.get("/exam", response_class=HTMLResponse)
def exam_mode_page(request: Request) -> HTMLResponse:
    """Renders the exam mode page.

    :return: The rendered HTML for the exam mode page.
    """
    templates = request.app.state.templates
    mode = getattr(request.app.state, 'mode', 'teacher')
    return templates.TemplateResponse(request, "exam_mode.html", {"mode": mode})
