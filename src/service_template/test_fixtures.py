"""
Herbruikbare test fixtures.
- 'client' werkt zonder DB (DATABASE_ENABLED=false in tests by default)
- Voor DB integration tests: gebruik @pytest.mark.integration en zorg zelf voor DB
"""
import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def reset_settings(monkeypatch):
    """Test-vriendelijke settings: alles uit, geen DB, console logs."""
    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    monkeypatch.setenv("LOG_FORMAT", "console")
    # Database default UIT in tests - integration tests zetten dit aan
    monkeypatch.setenv("DATABASE_ENABLED", "false")


@pytest.fixture
def auth_headers():
    """Headers met Bearer token voor secure endpoints (als auth aan staat)."""
    return {"Authorization": "Bearer test-token-12345"}


@pytest.fixture
def client():
    """TestClient voor de app. Zonder DB - voor unit en contract tests."""
    from fastapi.testclient import TestClient
    from src.main import app
    with TestClient(app) as c:
        yield c
