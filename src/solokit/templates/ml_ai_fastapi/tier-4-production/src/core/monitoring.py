"""
Prometheus metrics setup for monitoring
"""

from fastapi import Response  # type: ignore[import-not-found]
from prometheus_client import (  # type: ignore[import-not-found]
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# Create a custom registry
registry = CollectorRegistry()

# Request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
    registry=registry,
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    registry=registry,
)

# Application metrics
active_users = Gauge(
    "active_users",
    "Number of active users",
    registry=registry,
)

database_connections = Gauge(
    "database_connections",
    "Number of active database connections",
    registry=registry,
)

# Business metrics
items_created_total = Counter(
    "items_created_total",
    "Total number of items created",
    registry=registry,
)

items_deleted_total = Counter(
    "items_deleted_total",
    "Total number of items deleted",
    registry=registry,
)


def get_metrics() -> Response:
    """
    Generate Prometheus metrics response.

    Returns:
        Response: Prometheus metrics in text format
    """
    metrics = generate_latest(registry)
    return Response(content=metrics, media_type=CONTENT_TYPE_LATEST)
