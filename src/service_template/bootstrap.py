"""
Bootstrap functie - configureer een FastAPI service met alle enterprise dimensies.

Gebruik in elke service src/main.py:

    from src.service_template.bootstrap import create_app
    from src.routes import router as business_router

    app = create_app(
        title="My Service",
        version="0.1.0",
        business_routers=[business_router],
        readiness_checks={"db": check_db},
    )
"""
import uuid
import structlog
from contextlib import asynccontextmanager
from typing import Iterable
from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.service_template.settings import settings
from src.service_template.logging_config import setup_logging, get_logger
from src.service_template.health import create_health_router, ReadinessCheck
from src.service_template.metrics import create_metrics_router, metrics_middleware
from src.service_template.resilience import (
    request_size_middleware,
    request_timeout_middleware,
    security_headers_middleware,
)
from src.service_template.rate_limit import limiter


def create_app(
    title: str = None,
    version: str = None,
    business_routers: Iterable[APIRouter] = (),
    readiness_checks: dict[str, ReadinessCheck] = None,
) -> FastAPI:
    """Maak een FastAPI app met alle enterprise standaarden ingebouwd."""

    setup_logging(level=settings.log_level, fmt=settings.log_format)
    log = get_logger("bootstrap")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        log.info("service_starting",
                 service=settings.service_name,
                 version=settings.service_version,
                 environment=settings.environment,
                 port=settings.port,
                 auth_enabled=settings.auth_enabled,
                 rate_limit_enabled=settings.rate_limit_enabled)
        yield
        log.info("service_stopping", service=settings.service_name)

    app = FastAPI(
        title=title or settings.service_name,
        version=version or settings.service_version,
        description=f"Auto-generated microservice ({settings.environment} environment)",
        contact={"name": "AI Software Factory", "email": "ops@ai-factory.local"},
        license_info={"name": "Internal", "url": "https://github.com/davidvanc/ai-factory"},
        openapi_tags=[
            {"name": "health", "description": "Liveness and readiness probes"},
            {"name": "metrics", "description": "Prometheus metrics endpoint"},
        ],
        lifespan=lifespan,
    )

    app.state.service_name = settings.service_name

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
    if settings.rate_limit_enabled:
        app.add_middleware(SlowAPIMiddleware)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID middleware
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=req_id,
            method=request.method,
            path=request.url.path,
        )
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response

    # Security + resilience middleware (volgorde belangrijk)
    app.middleware("http")(security_headers_middleware)
    app.middleware("http")(request_timeout_middleware)
    app.middleware("http")(request_size_middleware)

    # Metrics middleware
    if settings.metrics_enabled:
        app.middleware("http")(metrics_middleware)

    # Standaard routes
    app.include_router(create_health_router(readiness_checks))
    if settings.metrics_enabled:
        app.include_router(create_metrics_router(settings.metrics_path))

    # Business routes
    for router in business_routers:
        app.include_router(router)

    return app


async def _rate_limit_handler(request, exc):
    from fastapi.responses import JSONResponse
    from fastapi import status
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": f"Rate limit exceeded: {exc.detail}"}
    )
