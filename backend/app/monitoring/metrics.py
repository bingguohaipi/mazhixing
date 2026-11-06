"""Prometheus metrics instrumentation."""

from __future__ import annotations

import time

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
SUBMISSIONS_TOTAL = Counter(
    "submissions_total",
    "Total code submissions",
    ["status"],
)


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/metrics", "/health"}:
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        path = request.url.path
        if len(path) > 80:
            path = path[:77] + "..."

        HTTP_REQUESTS_TOTAL.labels(request.method, path, str(response.status_code)).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(request.method, path).observe(duration)
        return response
