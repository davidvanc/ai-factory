"""
Resilience middleware en helpers:
- Request body size limit (anti-DoS)
- Per-request timeout
- Graceful shutdown helpers
- Security headers (HSTS, X-Frame-Options, etc.)
"""
import asyncio
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from src.service_template.settings import settings


async def request_size_middleware(request: Request, call_next):
    """Weiger requests met body groter dan max_request_body_bytes."""
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            size = int(content_length)
            if size > settings.max_request_body_bytes:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={
                        "detail": f"Request body too large ({size} bytes, max {settings.max_request_body_bytes})"
                    }
                )
        except ValueError:
            pass
    return await call_next(request)


async def request_timeout_middleware(request: Request, call_next):
    """Hard timeout per request."""
    try:
        return await asyncio.wait_for(
            call_next(request),
            timeout=settings.request_timeout_seconds
        )
    except asyncio.TimeoutError:
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={"detail": f"Request exceeded {settings.request_timeout_seconds}s timeout"}
        )


async def security_headers_middleware(request: Request, call_next):
    """Voeg standaard security headers toe aan responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # HSTS alleen in productie zinvol (vereist HTTPS)
    if settings.environment == "prod":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
