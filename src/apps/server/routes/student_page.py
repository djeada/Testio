"""This module defines a FastAPI router for rendering the student page."""
import sys

sys.path.append(".")
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from src.apps.server.database.configuration_data import parse_config_data

student_page_router: APIRouter = APIRouter()


@student_page_router.get("/student", response_class=HTMLResponse)
def student_page(request: Request) -> HTMLResponse:
    """Renders the student page where students can input and test their code.

    :return: The HTML content of the student page.
    """
    config_data = parse_config_data()
    templates = request.app.state.templates
    mode = getattr(request.app.state, 'mode', 'teacher')
    return templates.TemplateResponse(request, "student_page.html", {"config_data": config_data, "mode": mode})
