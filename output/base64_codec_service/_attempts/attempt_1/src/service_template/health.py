"""
Health en readiness endpoints volgens Kubernetes best practices.
- /health (liveness): is het proces überhaupt nog leven? Snel, geen externe checks.
- /ready (readiness): kan het proces verkeer aan? Checks downstream deps.
"""
from typing import Callable, Awaitable
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse


# Type voor readiness checks: async functie die (ok, message) teruggeeft
ReadinessCheck = Callable[[], Awaitable[tuple[bool, str]]]


def create_health_router(readiness_checks: dict[str, ReadinessCheck] = None) -> APIRouter:
    """
    Maak een APIRouter met /health en /ready endpoints.

    readiness_checks: dict van naam -> async check functie.
    Bv: {"database": check_db, "cache": check_redis}
    """
    router = APIRouter(tags=["health"])
    checks = readiness_checks or {}

    @router.get("/health", summary="Liveness probe")
    async def health():
        """Simpel: is het proces nog leven? Geen externe checks."""
        return {"status": "ok"}

    @router.get("/ready", summary="Readiness probe")
    async def ready():
        """Strenger: kan de service verkeer aan?"""
        if not checks:
            return {"status": "ready", "checks": {}}

        results = {}
        all_ok = True
        for name, check_fn in checks.items():
            try:
                ok, message = await check_fn()
                results[name] = {"ok": ok, "message": message}
                if not ok:
                    all_ok = False
            except Exception as e:
                results[name] = {"ok": False, "message": f"check raised: {e}"}
                all_ok = False

        if all_ok:
            return {"status": "ready", "checks": results}
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "checks": results}
        )

    return router
