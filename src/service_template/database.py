"""
Async database module met SQLAlchemy 2.0 + asyncpg.
- Twee modes: shared (centrale Postgres) of local (per-service Postgres)
- Connection pooling via SQLAlchemy
- Lifecycle handlers voor clean startup/shutdown
- Helpers voor sessions als FastAPI dependency
"""
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from src.service_template.settings import settings
from src.service_template.logging_config import get_logger

log = get_logger("database")


class Base(DeclarativeBase):
    """Base class voor SQLAlchemy models. Importeer dit en erf voor je tabellen."""
    pass


# Globale engine en session maker - opgezet bij startup
_engine: Optional[AsyncEngine] = None
_SessionLocal: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine() -> AsyncEngine:
    """Haal de globale engine op. Werpt error als niet geïnitialiseerd."""
    if _engine is None:
        raise RuntimeError("Database engine niet geïnitialiseerd - roep init_database() aan in startup")
    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Haal de session factory op."""
    if _SessionLocal is None:
        raise RuntimeError("Database session maker niet geïnitialiseerd")
    return _SessionLocal


async def init_database():
    """
    Initialiseer database connectie - aan te roepen in lifespan startup.
    Leest connection details uit settings.
    """
    global _engine, _SessionLocal

    if not settings.database_enabled:
        log.info("database_disabled_skip_init")
        return

    db_url = settings.database_url
    # Forceer async driver indien geen async-prefix is gegeven
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("sqlite:///"):
        db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

    log.info("database_initializing", mode=settings.database_mode, pool_size=settings.database_pool_size)

    engine_kwargs = {
        "echo": settings.database_echo,
    }
    # Pool args alleen voor echte DBs, niet voor SQLite
    if not db_url.startswith("sqlite"):
        engine_kwargs.update({
            "pool_size": settings.database_pool_size,
            "max_overflow": settings.database_pool_max_overflow,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        })

    _engine = create_async_engine(db_url, **engine_kwargs)

    _SessionLocal = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    log.info("database_initialized")


async def close_database():
    """Sluit alle DB connecties netjes - aan te roepen in lifespan shutdown."""
    global _engine
    if _engine is not None:
        log.info("database_closing")
        await _engine.dispose()
        _engine = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency die een AsyncSession levert.
    Gebruik in endpoints:
        async def my_endpoint(db: AsyncSession = Depends(get_db)):
            result = await db.execute(...)
    """
    if _SessionLocal is None:
        raise RuntimeError("Database niet geïnitialiseerd")

    async with _SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def database_health_check() -> tuple[bool, str]:
    """Health check voor /ready endpoint."""
    if not settings.database_enabled:
        return True, "disabled"
    try:
        from sqlalchemy import text
        async with _SessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True, "ok"
    except Exception as e:
        return False, f"db error: {str(e)[:100]}"
