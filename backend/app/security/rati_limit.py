import time
import redis
from app.config import settings
from fastapi import Request, HTTPException, status

# Initialize Redis client
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

def check_rate_limit(key: str, limit: int, window: int) -> bool:
    """
    Check if the request is within the rate limit.
    Uses a fixed window counter algorithm.
    Returns True if allowed, False if rate limit exceeded.
    """
    current = redis_client.get(key)
    if current is None:
        # Key doesn't exist, set it to 1 with expiration
        redis_client.setex(key, window, 1)
        return True
    else:
        current = int(current)
        if current >= limit:
            return False
        # Increment the counter
        redis_client.incr(key)
        return True

def get_rate_limit_key(prefix: str, identifier: str) -> str:
    """
    Generate a rate limit key.
    """
    return f"rate_limit:{prefix}:{identifier}"

# Rate limit dependencies for specific endpoints
def login_rate_limit(request: Request) -> None:
    """
    Rate limit for login endpoint.
    Uses IP address as identifier.
    """
    identifier = request.client.host if request.client else "unknown"
    key = get_rate_limit_key("login", identifier)
    if not check_rate_limit(key, settings.LOGIN_RATE_LIMIT_PER_MINUTE, 60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

def signup_rate_limit(request: Request) -> None:
    """
    Rate limit for signup endpoint.
    Uses IP address as identifier.
    """
    identifier = request.client.host if request.client else "unknown"
    key = get_rate_limit_key("signup", identifier)
    if not check_rate_limit(key, settings.SIGNUP_RATE_LIMIT_PER_MINUTE, 60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many signups. Please try again later.",
        )

def forgot_password_rate_limit(request: Request) -> None:
    """
    Rate limit for forgot password endpoint.
    Uses IP address as identifier.
    """
    identifier = request.client.host if request.client else "unknown"
    key = get_rate_limit_key("forgot_password", identifier)
    if not check_rate_limit(key, settings.FORGOT_PASSWORD_RATE_LIMIT_PER_HOUR, 3600):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset requests. Please try again later.",
        )

def resend_verification_rate_limit(request: Request) -> None:
    """
    Rate limit for resend verification endpoint.
    Uses IP address as identifier.
    """
    identifier = request.client.host if request.client else "unknown"
    key = get_rate_limit_key("resend_verification", identifier)
    if not check_rate_limit(key, settings.RESEND_VERIFICATION_RATE_LIMIT_PER_HOUR, 3600):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many verification resend requests. Please try again later.",
        )