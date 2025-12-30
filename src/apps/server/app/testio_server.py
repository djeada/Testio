"""A custom FastAPI application for the TestioServer."""
import sys
from pathlib import Path

sys.path.append(".")

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from src.apps.server.database.database import Database
from src.apps.server.routes.execute_tests import execute_tests_router
from src.apps.server.routes.index_page import index_page_router
from src.apps.server.routes.update_test_suite import update_test_suite_router
from src.apps.server.routes.exam_mode import exam_mode_page_router
from src.apps.server.routes.homework_mode import homework_mode_page_router
from src.apps.server.routes.homework_submission import homework_submission_router
from src.apps.server.routes.exam_session import exam_session_router
from src.apps.server.routes.student_exam import student_exam_router
from src.apps.server.routes.student_page import student_page_router
from src.apps.server.routes.student_submission import student_submission_router
from src.apps.server.routes.health import health_router
from src.apps.server.routes.statistics import stats_router
from src.apps.server.routes.batch_execution import batch_router
from src.apps.server.routes.export import export_router
from src.apps.server.middleware import RequestLoggingMiddleware, ErrorHandlingMiddleware


# API version
API_VERSION = "1.0.0"


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    :return: Configured FastAPI application instance.
    """
    app = FastAPI(
        title="Testio",
        description="A flexible and powerful testing framework for verifying application outputs. "
                    "Features include CLI and web interfaces, homework and exam modes, batch testing, "
                    "and comprehensive statistics.",
        version=API_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # Add CORS middleware for cross-origin requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify allowed origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add custom middleware
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)

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
        # Core functionality
        index_page_router,
        update_test_suite_router,
        execute_tests_router,
        # Homework mode
        homework_mode_page_router,
        homework_submission_router,
        # Exam mode
        exam_mode_page_router,
        exam_session_router,
        student_exam_router,
        # Student pages
        student_page_router,
        student_submission_router,
        # New API features
        health_router,
        stats_router,
        batch_router,
        export_router,
    ]

    for router in routers:
        app.include_router(router)

    return app


# Create the app instance
app = create_app()
