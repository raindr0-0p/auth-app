import secrets
from fastapi import Request, Response, HTTPException, status
from app.config import settings

def generate_csrf_token() -> str:
    """
    Generate a cryptographically secure random CSRF token.
    """
    return secrets.token_urlsafe(32)

def set_csrf_cookie(response: Response, csrf_token: str) -> None:
    """
    Set the CSRF token cookie (not HttpOnly so JavaScript can read it).
    """
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        max_age=settings.SESSION_EXPIRE_MINUTES * 60,  # Same as session
        path=settings.COOKIE_PATH,
        secure=settings.COOKIE_SECURE,  # Same as session cookie
        httponly=False,  # JavaScript can read this one
        samesite=settings.COOKIE_SAMESITE,
    )

def clear_csrf_cookie(response: Response) -> None:
    """
    Clear the CSRF token cookie.
    """
    response.delete_cookie(
        key="csrf_token",
        path=settings.COOKIE_PATH,
    )

async def csrf_protection(request: Request) -> None:
    """
    Dependency to validate CSRF token for state-changing requests.
    Uses the double-submit cookie method: the CSRF token must be present in both
    the cookie and the request header (X-CSRF-Token) and they must match.
    """
    # Only validate for state-changing methods
    if request.method.upper() in ("GET", "HEAD", "OPTIONS", "TRACE"):
        return

    # Get CSRF token from cookie and header
    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get(settings.CSRF_HEADER_NAME)

    if not csrf_cookie or not csrf_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing",
        )

    if csrf_cookie != csrf_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token mismatch",
        )