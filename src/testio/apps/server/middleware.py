"""Middleware components for the Testio server."""

import logging
import time
from datetime import datetime
from typing import Callable, Optional

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from testio.apps.server.settings import get_max_request_bytes

logger = logging.getLogger("testio.server")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log incoming requests and outgoing responses.

        :param request: The incoming request
        :param call_next: The next middleware or route handler
        :return: The response
        """
        # Generate a request ID for tracing
        request_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{id(request)}"

        # Record start time
        start_time = time.time()

        # Log the incoming request
        logger.info(
            f"Request {request_id}: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        try:
            # Process the request
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.4f}"

            # Log the response
            logger.info(
                f"Response {request_id}: {response.status_code} "
                f"(took {process_time:.4f}s)"
            )

            return response

        except Exception as e:
            # Log the error
            process_time = time.time() - start_time
            logger.error(f"Error {request_id}: {str(e)} (took {process_time:.4f}s)")
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Last-resort handler for exceptions that escaped the route handlers.

    Deliberate errors (``HTTPException``, request validation) are rendered by
    FastAPI before they reach this middleware. Anything arriving here is
    unexpected, so the client gets a generic message - never ``str(e)``,
    which could reveal paths, SQL or other internals - and the details are
    logged server-side.
    """

    @staticmethod
    def _error(status_code: int, error: str, message: str) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content={
                "error": error,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Handle errors and return consistent error responses.

        :param request: The incoming request
        :param call_next: The next middleware or route handler
        :return: The response
        """
        try:
            return await call_next(request)
        except ValueError as e:
            logger.warning(f"Validation error: {e}", exc_info=True)
            return self._error(400, "validation_error", "Invalid request")
        except PermissionError as e:
            logger.warning(f"Permission error: {e}", exc_info=True)
            return self._error(403, "permission_denied", "Permission denied")
        except FileNotFoundError as e:
            logger.warning(f"Resource not found: {e}", exc_info=True)
            return self._error(404, "not_found", "Resource not found")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return self._error(500, "internal_error", "An unexpected error occurred")


class BodySizeLimitMiddleware:
    """Reject request bodies larger than TESTIO_MAX_REQUEST_SIZE_MB with 413.

    Checked against ``Content-Length`` up front and against the bytes actually
    received (chunked uploads), so an oversized body is never fully buffered.
    Implemented as plain ASGI middleware so it can wrap the body stream.
    """

    def __init__(self, app: ASGIApp, max_bytes: Optional[int] = None) -> None:
        self.app = app
        self._max_bytes = max_bytes

    def _limit(self) -> int:
        return (
            self._max_bytes if self._max_bytes is not None else get_max_request_bytes()
        )

    @staticmethod
    def _too_large_response(limit: int) -> JSONResponse:
        return JSONResponse(
            status_code=413,
            content={
                "detail": "Request body exceeds the maximum allowed size of "
                f"{limit / (1024 * 1024):g} MB"
            },
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        limit = self._limit()
        if scope["type"] != "http" or limit <= 0:
            await self.app(scope, receive, send)
            return

        for name, value in scope.get("headers", []):
            if name == b"content-length":
                try:
                    declared = int(value)
                except ValueError:
                    declared = 0
                if declared > limit:
                    await self._too_large_response(limit)(scope, receive, send)
                    return

        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    # FastAPI re-raises HTTPExceptions raised while reading
                    # the body, so this becomes a normal 413 response.
                    raise HTTPException(
                        status_code=413,
                        detail="Request body exceeds the maximum allowed size of "
                        f"{limit / (1024 * 1024):g} MB",
                    )
            return message

        await self.app(scope, limited_receive, send)
