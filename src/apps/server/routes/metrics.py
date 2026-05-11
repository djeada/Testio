"""Routes for exposing application metrics and monitoring data."""

from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from src.apps.server.auth import require_teacher_auth
from src.apps.server.settings import get_app_database_path
from src.core.metrics import get_metrics_collector
from src.core.caching import MemoryCache

metrics_router: APIRouter = APIRouter(tags=["Metrics"])


class MetricsResponse(BaseModel):
    """Response model for metrics endpoint."""

    timestamp: str
    application: str
    version: str
    metrics: Dict[str, Any]


class CacheStatsResponse(BaseModel):
    """Response model for cache statistics."""

    timestamp: str
    cache_stats: Dict[str, Any]


class SystemStatsResponse(BaseModel):
    """Response model for system statistics."""

    timestamp: str
    database: Dict[str, Any]
    execution_queue: Dict[str, Any]
    rate_limiter: Dict[str, Any]


@metrics_router.get("/api/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    """
    Get application performance metrics.

    Returns counters, gauges, and timing statistics for various
    operations in the application.

    :return: MetricsResponse with collected metrics
    """
    collector = get_metrics_collector()
    return MetricsResponse(
        timestamp=datetime.now().isoformat(),
        application="Testio",
        version="1.0.0",
        metrics=collector.get_all_metrics(),
    )


@metrics_router.get("/api/metrics/cache", response_model=CacheStatsResponse)
async def get_cache_stats(request: Request) -> CacheStatsResponse:
    """
    Get cache statistics.

    Returns information about cache hit rates, size, and configuration.

    :param request: FastAPI request object
    :return: CacheStatsResponse with cache statistics
    """
    # Get cache from app state if available, otherwise use global cache
    cache = getattr(request.app.state, "cache", None)
    if cache and isinstance(cache, MemoryCache):
        stats = cache.get_stats()
    else:
        from src.core.caching.memory_cache import get_global_cache

        stats = get_global_cache().get_stats()

    return CacheStatsResponse(timestamp=datetime.now().isoformat(), cache_stats=stats)


@metrics_router.get("/api/metrics/system", response_model=SystemStatsResponse)
async def get_system_stats(request: Request) -> SystemStatsResponse:
    """
    Get comprehensive system statistics.

    Returns statistics from the database, execution queue,
    and rate limiter components.

    :param request: FastAPI request object
    :return: SystemStatsResponse with system statistics
    """
    # Database stats
    db_stats = {}
    try:
        from src.apps.server.database.connection_pool import get_connection_pool

        pool = get_connection_pool(get_app_database_path())
        db_stats = pool.get_stats()
    except Exception:
        db_stats = {"error": "Could not retrieve database stats"}

    # Execution queue stats
    queue_stats = {}
    try:
        from src.core.execution.queue import get_execution_queue

        queue = get_execution_queue()
        queue_stats = queue.get_stats()
    except Exception:
        queue_stats = {"error": "Could not retrieve queue stats"}

    # Rate limiter stats
    rate_limiter_stats: Dict[str, Any] = {}
    try:
        from src.apps.server.rate_limiter import get_active_rate_limiter

        mw = get_active_rate_limiter()
        if mw is not None:
            rate_limiter_stats = mw.get_limiter_stats()
        else:
            rate_limiter_stats = {"status": "not_initialized"}
    except Exception:
        rate_limiter_stats = {"error": "Could not retrieve rate limiter stats"}

    return SystemStatsResponse(
        timestamp=datetime.now().isoformat(),
        database=db_stats,
        execution_queue=queue_stats,
        rate_limiter=rate_limiter_stats,
    )


@metrics_router.post("/api/metrics/reset")
async def reset_metrics(
    _auth: None = Depends(require_teacher_auth),
) -> Dict[str, str]:
    """
    Reset all metrics counters.

    This is useful for starting fresh measurements or after
    a deployment.

    :return: Confirmation message
    """
    collector = get_metrics_collector()
    collector.reset()
    return {
        "status": "success",
        "message": "All metrics have been reset",
        "timestamp": datetime.now().isoformat(),
    }
