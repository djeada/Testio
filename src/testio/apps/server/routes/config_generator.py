"""This module defines a FastAPI router for rendering the config generator page."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from testio.apps.server.auth import teacher_page_redirect

config_generator_page_router: APIRouter = APIRouter()


@config_generator_page_router.get(
    "/config-generator", response_class=HTMLResponse, response_model=None
)
def config_generator_page(request: Request) -> Response:
    """Renders the config generator page for teachers.

    :return: The HTML content of the config generator page.
    """
    redirect = teacher_page_redirect(request)
    if redirect is not None:
        return redirect
    templates = request.app.state.templates
    mode = getattr(request.app.state, "mode", "teacher")
    return templates.TemplateResponse(request, "config_generator.html", {"mode": mode})
