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

from src.service_template.settings import settings
from src.service_template.logging_config import setup_logging, get_logger
from src.service_template.health import create_health_router, ReadinessCheck
from src.service_template.metrics import create_metrics_router, metrics_middleware


def create_app(
    title: str = None,
    version: str = None,
    business_routers: Iterable[APIRouter] = (),
    readiness_checks: dict[str, ReadinessCheck] = None,
) -> FastAPI:
    """Maak een FastAPI app met alle enterprise standaarden ingebouwd."""

    # Logging eerst opzetten
    setup_logging(level=settings.log_level, fmt=settings.log_format)
    log = get_logger("bootstrap")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        log.info("service_starting", service=settings.service_name, version=settings.service_version,
                 environment=settings.environment, port=settings.port)
        yield
        log.info("service_stopping", service=settings.service_name)

    app = FastAPI(
        title=title or settings.service_name,
        version=version or settings.service_version,
        lifespan=lifespan,
    )
    app.state.service_name = settings.service_name

    # Request ID middleware - voor traceability door logs
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

    # Metrics middleware
    if settings.metrics_enabled:
        app.middleware("http")(metrics_middleware)

    # Standaard routes: /health, /ready, /metrics
    app.include_router(create_health_router(readiness_checks))
    if settings.metrics_enabled:
        app.include_router(create_metrics_router(settings.metrics_path))

    # Business routes
    for router in business_routers:
        app.include_router(router)

    return app
