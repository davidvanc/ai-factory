"""
Herbruikbare test fixtures voor elke gegenereerde service.
Importeer in tests/conftest.py:

    from src.service_template.test_fixtures import client, anyio_backend, auth_headers, reset_settings
"""
import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def reset_settings(monkeypatch):
    """Configureer test-vriendelijke settings. Database -> in-memory SQLite."""
    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    monkeypatch.setenv("LOG_FORMAT", "console")
    # SQLite in-memory voor tests - geen externe DB nodig
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")


@pytest.fixture
def auth_headers():
    """Headers met Bearer token voor secure endpoints (als auth aan staat)."""
    return {"Authorization": "Bearer test-token-12345"}


@pytest.fixture
async def _ensure_tables():
    """
    Maak alle tabellen in test-DB. Wordt automatisch gerund door 'client' fixture.
    Vereist dat alle modellen geïmporteerd zijn.
    """
    from src.service_template.database import init_database, get_engine, Base, close_database

    # Probeer modellen te importeren - safe als ze niet bestaan
    try:
        import src.models  # noqa: F401
    except ImportError:
        pass

    await init_database()
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await close_database()


@pytest.fixture
def client(_ensure_tables):
    """TestClient voor de app, met tabellen aangemaakt in in-memory SQLite."""
    from fastapi.testclient import TestClient
    from src.main import app
    with TestClient(app) as c:
        yield c
