"""
Lifespan handlers: startup en graceful shutdown.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.service_template.logging_config import get_logger

log = get_logger("lifespan")


@asynccontextmanager
async def default_lifespan(app: FastAPI):
    """Standaard lifespan: log start/stop, plek voor resource setup."""
    log.info("service_starting", service=getattr(app.state, "service_name", "unknown"))

    # Hier kan je in je eigen code resources opzetten:
    # app.state.db = await create_db_pool()
    # app.state.http_client = httpx.AsyncClient()

    yield

    # Graceful shutdown
    log.info("service_stopping")
    # Sluit resources:
    # await app.state.db.close()
    # await app.state.http_client.aclose()
