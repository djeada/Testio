"""This module defines a FastAPI router for rendering the homework mode web page."""
import sys

sys.path.append(".")

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from src.apps.server.database.configuration_data import parse_config_data

homework_mode_page_router: APIRouter = APIRouter()


@homework_mode_page_router.get("/homework", response_class=HTMLResponse)
def homework_mode_page(request: Request) -> HTMLResponse:
    """Renders a web page for the homework mode and passes the configuration data to the template.

    :return: The HTML content of the homework mode web page.
    """
    config_data = parse_config_data()
    templates = request.app.state.templates
    mode = getattr(request.app.state, 'mode', 'teacher')
    return templates.TemplateResponse(request, "homework_mode.html", {"config_data": config_data, "mode": mode})
