"""Middleware components for the Testio server."""
import sys
import time
import logging
from typing import Callable
from datetime import datetime

sys.path.append(".")

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
            logger.error(
                f"Error {request_id}: {str(e)} (took {process_time:.4f}s)"
            )
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for consistent error handling."""
    
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
            logger.warning(f"Validation error: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={
                    "error": "validation_error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
        except PermissionError as e:
            logger.warning(f"Permission error: {str(e)}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": "permission_denied",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
        except FileNotFoundError as e:
            logger.warning(f"Resource not found: {str(e)}")
            return JSONResponse(
                status_code=404,
                content={
                    "error": "not_found",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_error",
                    "message": "An unexpected error occurred",
                    "timestamp": datetime.now().isoformat()
                }
            )
