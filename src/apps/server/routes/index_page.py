"""This module defines a FastAPI router for rendering the index page."""
import sys

sys.path.append(".")
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from src.apps.server.database.configuration_data import parse_config_data

index_page_router: APIRouter = APIRouter()


@index_page_router.get("/", response_class=HTMLResponse)
def index_page(request: Request) -> HTMLResponse:
    """Renders the index page and passes the configuration data to the template.

    :return: The HTML content of the index page.
    """
    config_data = parse_config_data()
    templates = request.app.state.templates
    mode = getattr(request.app.state, 'mode', 'teacher')
    return templates.TemplateResponse(request, "index.html", {"config_data": config_data, "mode": mode})
