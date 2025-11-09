"""
Prometheus metrics endpoint
"""

from fastapi import APIRouter, Response  # type: ignore[import-not-found]
from src.core.monitoring import get_metrics  # type: ignore[import-not-found]

router = APIRouter()


@router.get("/metrics")
async def metrics() -> Response:
    """
    Prometheus metrics endpoint.

    Returns:
        Response: Prometheus metrics in text format
    """
    return get_metrics()
