"""
Bearer token authenticatie via Authorization header.
- Opt-in via auth_enabled setting
- Tokens komen uit auth_tokens setting (comma-separated)
- 401 bij ontbreken, 403 bij ongeldig
- Endpoints kunnen via dependency injection beschermd worden
"""
from typing import Optional
from fastapi import HTTPException, Header, status
from src.service_template.settings import settings


async def verify_bearer_token(
    authorization: Optional[str] = Header(default=None)
) -> str:
    """
    FastAPI dependency die Bearer token valideert.
    Gebruik in endpoints: token = Depends(verify_bearer_token)

    Als auth_enabled=False, returnt deze "anonymous" zonder check.
    """
    if not settings.auth_enabled:
        return "anonymous"

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing. Use: Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must start with 'Bearer '",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = authorization[7:].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty Bearer token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    valid_tokens = settings.auth_tokens_set
    if not valid_tokens:
        # Auth enabled maar geen tokens geconfigureerd - log waarschuwing en weiger
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth enabled but no tokens configured (set AUTH_TOKENS env var)"
        )

    if token not in valid_tokens:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Bearer token"
        )

    return token
