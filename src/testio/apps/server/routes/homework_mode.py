"""This module defines a FastAPI router for rendering the homework mode web page."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from testio.apps.server.auth import teacher_page_redirect
from testio.apps.server.database.configuration_data import parse_config_data

homework_mode_page_router: APIRouter = APIRouter()


@homework_mode_page_router.get(
    "/homework", response_class=HTMLResponse, response_model=None
)
def homework_mode_page(request: Request) -> Response:
    """Renders a web page for the homework mode and passes the configuration data to the template.

    :return: The HTML content of the homework mode web page.
    """
    redirect = teacher_page_redirect(request)
    if redirect is not None:
        return redirect
    config_data = parse_config_data()
    templates = request.app.state.templates
    mode = getattr(request.app.state, "mode", "teacher")
    return templates.TemplateResponse(
        request, "homework_mode.html", {"config_data": config_data, "mode": mode}
    )
