"""A custom FastAPI application for the TestioServer."""

import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.apps.server.database.connection_pool import get_connection_pool
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
from src.apps.server.routes.config_generator import config_generator_page_router
from src.apps.server.routes.metrics import metrics_router
from src.apps.server.routes.exercise_submission import exercise_router
from src.apps.server.settings import (
    get_app_database_path,
    get_log_level,
    get_log_format,
)
from src.apps.server.middleware import RequestLoggingMiddleware, ErrorHandlingMiddleware
from src.apps.server.rate_limiter import RateLimitMiddleware, RateLimitConfig
from src.core.caching import MemoryCache
from src.core.execution.queue import get_execution_queue
from src.core.logging_config import configure_logging, get_logger
from src.core.metrics import get_metrics_collector

# Configure structured logging as early as possible.
configure_logging(level=get_log_level(), json_format=get_log_format() == "json")
_log = get_logger(__name__)

# API version
API_VERSION = "1.0.0"

# Valid application modes
AppMode = Literal["teacher", "student"]


def _get_cors_settings() -> tuple[list[str], bool]:
    configured_origins = os.getenv("TESTIO_ALLOW_ORIGINS", "")
    allow_origins = [
        origin.strip() for origin in configured_origins.split(",") if origin.strip()
    ]
    allow_credentials = bool(allow_origins) and allow_origins != ["*"]
    return allow_origins, allow_credentials


def create_app(mode: AppMode = "teacher") -> FastAPI:
    """
    Create and configure the FastAPI application.

    :param mode: Application mode - 'teacher' (default) for full access,
                 'student' for student-focused UI with limited features.
    :return: Configured FastAPI application instance.
    """
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    if not os.environ.get("TESTIO_TEACHER_API_KEY"):
        logging.getLogger("testio.auth").warning(
            "TESTIO_TEACHER_API_KEY is not set — teacher endpoints are unprotected (dev mode)"
        )

    # Customize app description based on mode
    if mode == "student":
        description = (
            "Testio Student Mode - Submit your code, test it, and get instant feedback. "
            "Perfect for learning and practicing programming."
        )
        title = "Testio - Student Mode"
    else:
        description = (
            "A flexible and powerful testing framework for verifying application outputs. "
            "Features include CLI and web interfaces, homework and exam modes, batch testing, "
            "and comprehensive statistics."
        )
        title = "Testio - Teacher Mode"

    openapi_tags = [
        {
            "name": "Health",
            "description": "Health, liveness, and readiness endpoints.",
        },
        {
            "name": "Statistics",
            "description": "Aggregated statistics and reporting endpoints.",
        },
        {
            "name": "Batch Execution",
            "description": "Batch execution endpoints for teacher workflows.",
        },
        {
            "name": "Export",
            "description": "Export endpoints for results and reports.",
        },
        {
            "name": "Metrics",
            "description": "Operational metrics and monitoring endpoints.",
        },
    ]

    app = FastAPI(
        title=title,
        description=description,
        version=API_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        openapi_tags=openapi_tags,
    )

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
        )
        schema.setdefault("components", {}).setdefault("securitySchemes", {})[
            "ApiKeyAuth"
        ] = {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
        }
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi

    # Add CORS middleware for cross-origin requests
    allow_origins, allow_credentials = _get_cors_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add custom middleware
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)

    # Add rate limiting middleware for API protection
    rate_limit_config = RateLimitConfig(
        requests_per_minute=120,  # 2 requests per second average
        requests_per_second=20,  # Allow bursts
        burst_size=30,
    )
    app.add_middleware(RateLimitMiddleware, config=rate_limit_config)

    # Reference to the shared database pool
    app.state.db = get_connection_pool(get_app_database_path())

    # Initialize application cache
    app.state.cache = MemoryCache(default_ttl=300.0, max_size=1000)

    # Initialize and start the execution queue (resource-limits concurrent test runs)
    app.state.execution_queue = get_execution_queue()

    # Initialize metrics collector
    app.state.metrics = get_metrics_collector()

    # Store the application mode in app state
    app.state.mode = mode

    _log.info("Testio server started", extra={"mode": mode, "version": API_VERSION})

    # Get the path to static and templates directories
    server_dir = Path(__file__).parent.parent
    static_dir = server_dir / "static"
    templates_dir = server_dir / "templates"

    # Mount static files
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Store templates in app state for access in routes
    app.state.templates = Jinja2Templates(directory=str(templates_dir))

    # Register routers based on mode
    if mode == "student":
        # Student mode: Limited set of routes focused on code submission and testing
        routers = [
            # Core functionality for students
            index_page_router,
            execute_tests_router,
            # Student pages
            student_page_router,
            student_submission_router,
            # Student exam access
            student_exam_router,
            # Health check (for monitoring)
            health_router,
        ]
    else:
        # Teacher mode: Full access to all features
        routers = [
            # Core functionality
            index_page_router,
            update_test_suite_router,
            execute_tests_router,
            # Config generator
            config_generator_page_router,
            # Homework mode
            homework_mode_page_router,
            homework_submission_router,
            # Exam mode
            exam_mode_page_router,
            exam_session_router,
            student_exam_router,
            # Student pages (for teacher to preview)
            student_page_router,
            student_submission_router,
            # New API features
            health_router,
            stats_router,
            batch_router,
            export_router,
            # Metrics and monitoring
            metrics_router,
            # Exercise submission (immediate self-service execution)
            exercise_router,
        ]

    for router in routers:
        app.include_router(router)

    return app


# Create the default app instance (teacher mode for backward compatibility)
app = create_app(mode="teacher")
