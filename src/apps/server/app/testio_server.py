"""A custom FastAPI application for the TestioServer."""
import sys
from pathlib import Path

sys.path.append(".")

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.apps.server.database.database import Database
from src.apps.server.routes.execute_tests import execute_tests_router
from src.apps.server.routes.index_page import index_page_router
from src.apps.server.routes.update_test_suite import update_test_suite_router
from src.apps.server.routes.exam_mode import exam_mode_page_router
from src.apps.server.routes.homework_mode import homework_mode_page_router


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    :return: Configured FastAPI application instance.
    """
    app = FastAPI(title="Testio", description="A flexible and powerful testing framework")

    # Reference to the custom database class
    app.state.db = Database("testio.db")

    # Get the path to static and templates directories
    server_dir = Path(__file__).parent.parent
    static_dir = server_dir / "static"
    templates_dir = server_dir / "templates"

    # Mount static files
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Store templates in app state for access in routes
    app.state.templates = Jinja2Templates(directory=str(templates_dir))

    # Register all routers
    routers = [
        index_page_router,
        update_test_suite_router,
        execute_tests_router,
        homework_mode_page_router,
        exam_mode_page_router,
    ]

    for router in routers:
        app.include_router(router)

    return app


# Create the app instance
app = create_app()
