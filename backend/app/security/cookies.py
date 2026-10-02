from fastapi import Request, Response
from app.config import settings

def set_session_cookie(response: Response, session_token: str) -> None:
    """
    Set the session cookie with appropriate security attributes.
    """
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=session_token,
        max_age=settings.SESSION_EXPIRE_MINUTES * 60,  # Convert minutes to seconds
        path=settings.COOKIE_PATH,
        secure=settings.COOKIE_SECURE,  # True in production
        httponly=True,  # Not accessible via JavaScript
        samesite=settings.COOKIE_SAMESITE,  # Protection against CSRF
    )

def clear_session_cookie(response: Response) -> None:
    """
    Clear the session cookie.
    """
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        path=settings.COOKIE_PATH,
    )