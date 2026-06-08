"""
Prometheus metrics collection
"""

import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from prometheus_client import CollectorRegistry

# Create a custom registry
REGISTRY = CollectorRegistry()

# HTTP request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=REGISTRY
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=REGISTRY
)

# Business metrics
orders_created_total = Counter(
    'orders_created_total',
    'Total orders created',
    ['status'],
    registry=REGISTRY
)

payments_processed_total = Counter(
    'payments_processed_total',
    'Total payments processed',
    ['status', 'method'],
    registry=REGISTRY
)

users_registered_total = Counter(
    'users_registered_total',
    'Total users registered',
    registry=REGISTRY
)

# Active users gauge
active_users = Gauge(
    'active_users',
    'Number of active users',
    registry=REGISTRY
)

# Database connection pool metrics
db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections',
    registry=REGISTRY
)

db_connections_idle = Gauge(
    'db_connections_idle',
    'Number of idle database connections',
    registry=REGISTRY
)

# Cache metrics
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    registry=REGISTRY
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    registry=REGISTRY
)


def get_metrics():
    """Get Prometheus metrics"""
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )
