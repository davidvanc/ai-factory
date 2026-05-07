"""
Herbruikbare test fixtures voor elke gegenereerde service.
Importeer in tests/conftest.py:

    from src.service_template.test_fixtures import client, anyio_backend

Levert een TestClient die volledig werkende app start zonder Docker.
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
def client():
    """TestClient voor de app. Geen netwerk, geen Docker, snelle tests."""
    from src.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers():
    """Headers met Bearer token voor secure endpoints (als auth aan staat)."""
    return {"Authorization": "Bearer test-token-12345"}


@pytest.fixture(autouse=True)
def reset_settings(monkeypatch):
    """Zet auth uit tijdens tests om endpoints toegankelijk te houden."""
    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    monkeypatch.setenv("LOG_FORMAT", "console")
