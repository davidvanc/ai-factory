"""
Prometheus metrics: requests, latency, errors.
Custom-gebouwd voor volle controle (geen prometheus-fastapi-instrumentator).
"""
import time
from fastapi import APIRouter, Request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST


# Standaard metrics
REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"]
)

REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

REQUEST_ERRORS_TOTAL = Counter(
    "http_request_errors_total",
    "Total HTTP requests that resulted in 5xx",
    ["method", "path"]
)


async def metrics_middleware(request: Request, call_next):
    """Track elke request: duration, status, errors."""
    method = request.method
    # Use route path template (bv "/users/{id}") niet de echte URL
    # zodat we niet een metric per user_id krijgen
    path = request.url.path
    if request.scope.get("route"):
        path = request.scope["route"].path

    start = time.monotonic()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception:
        REQUEST_ERRORS_TOTAL.labels(method=method, path=path).inc()
        raise
    finally:
        duration = time.monotonic() - start
        REQUEST_DURATION_SECONDS.labels(method=method, path=path).observe(duration)
        REQUESTS_TOTAL.labels(
            method=method,
            path=path,
            status_code=str(status_code)
        ).inc()
        if status_code >= 500:
            REQUEST_ERRORS_TOTAL.labels(method=method, path=path).inc()


def create_metrics_router(path: str = "/metrics") -> APIRouter:
    """APIRouter die /metrics serveert in Prometheus exposition formaat."""
    router = APIRouter(tags=["metrics"])

    @router.get(path, include_in_schema=False)
    async def metrics():
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return router
