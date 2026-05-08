"""
Rate limiting via slowapi met Redis backend.
- Opt-in via rate_limit_enabled setting
- Per IP rate limiting (default 60 req/min)
- Redis-backed: schaalt over meerdere worker processen
- Fallback naar in-memory bij Redis verbinding-fail (degraded mode)
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from src.service_template.settings import settings
from src.service_template.logging_config import get_logger

log = get_logger("rate_limit")


def create_limiter() -> Limiter:
    """
    Maak een Limiter instance.
    - Met Redis als backend wanneer mogelijk
    - In-memory fallback bij verbinding-fail
    """
    if not settings.rate_limit_enabled:
        # Limiter die nooit limiteert - veiligheidsnet
        return Limiter(key_func=get_remote_address, enabled=False)

    try:
        # Probeer Redis backend
        limiter = Limiter(
            key_func=get_remote_address,
            storage_uri=settings.rate_limit_redis_url,
            default_limits=[f"{settings.rate_limit_per_minute}/minute"],
            strategy="fixed-window",
        )
        log.info("rate_limiter_using_redis", url=settings.rate_limit_redis_url)
        return limiter
    except Exception as e:
        # Fallback naar in-memory
        log.warning("rate_limiter_redis_failed_fallback_memory", error=str(e))
        return Limiter(
            key_func=get_remote_address,
            default_limits=[f"{settings.rate_limit_per_minute}/minute"],
        )


# Singleton
limiter = create_limiter()
