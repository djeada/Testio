"""This module defines a FastAPI router for the exam mode page."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from testio.apps.server.auth import teacher_page_redirect

exam_mode_page_router = APIRouter()


@exam_mode_page_router.get("/exam", response_class=HTMLResponse, response_model=None)
def exam_mode_page(request: Request) -> Response:
    """Renders the exam mode page.

    :return: The rendered HTML for the exam mode page.
    """
    redirect = teacher_page_redirect(request)
    if redirect is not None:
        return redirect
    templates = request.app.state.templates
    mode = getattr(request.app.state, "mode", "teacher")
    return templates.TemplateResponse(request, "exam_mode.html", {"mode": mode})
