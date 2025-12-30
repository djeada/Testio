"""This module defines FastAPI routes for health checks and system status."""
import sys
from datetime import datetime
from typing import Dict, Any

sys.path.append(".")

from fastapi import APIRouter, Request
from pydantic import BaseModel

health_router: APIRouter = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str
    timestamp: str
    version: str


class StatusResponse(BaseModel):
    """Response model for status endpoint."""
    status: str
    timestamp: str
    version: str
    uptime_seconds: float
    database_connected: bool


# Store the server start time
_server_start_time = datetime.now()


@health_router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """
    Simple health check endpoint.
    Returns the server status, current timestamp, and API version.
    
    :return: HealthResponse with status information
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )


@health_router.get("/api/status", response_model=StatusResponse)
def api_status(request: Request) -> StatusResponse:
    """
    Detailed status endpoint with system information.
    
    :param request: The FastAPI request object
    :return: StatusResponse with detailed status information
    """
    current_time = datetime.now()
    uptime = (current_time - _server_start_time).total_seconds()
    
    # Check database connectivity
    db_connected = False
    try:
        db = request.app.state.db
        if db:
            db_connected = True
    except Exception:
        pass
    
    return StatusResponse(
        status="running",
        timestamp=current_time.isoformat(),
        version="1.0.0",
        uptime_seconds=round(uptime, 2),
        database_connected=db_connected
    )
