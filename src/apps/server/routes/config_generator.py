"""This module defines a FastAPI router for rendering the config generator page."""
import sys

sys.path.append(".")

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

config_generator_page_router: APIRouter = APIRouter()


@config_generator_page_router.get("/config-generator", response_class=HTMLResponse)
def config_generator_page(request: Request) -> HTMLResponse:
    """Renders the config generator page for teachers.

    :return: The HTML content of the config generator page.
    """
    templates = request.app.state.templates
    mode = getattr(request.app.state, 'mode', 'teacher')
    return templates.TemplateResponse(request, "config_generator.html", {"mode": mode})
