from pydantic import BaseSettings, PostgresDsn, AnyHttpUrl, EmailStr, validator
from typing import Optional, List
import secrets

class Settings(BaseSettings):
    # Database
    DATABASE_URL: PostgresDsn

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # For production, set via environment variable

    # Frontend
    FRONTEND_URL: AnyHttpUrl = "http://localhost:5173"

    # Session
    SESSION_EXPIRE_MINUTES: int = 60  # 1 hour

    # Token expiration
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30  # 30 minutes
    EMAIL_VERIFICATION_EXPIRE_MINUTES: int = 60  # 60 minutes

    # Rate limiting
    LOGIN_RATE_LIMIT_PER_MINUTE: int = 5
    SIGNUP_RATE_LIMIT_PER_MINUTE: int = 3
    FORGOT_PASSWORD_RATE_LIMIT_PER_HOUR: int = 3
    RESEND_VERIFICATION_RATE_LIMIT_PER_HOUR: int = 3

    # Environment
    ENVIRONMENT: str = "development"

    # Email settings (for development, we'll use console)
    # In production, you would set SMTP settings
    EMAILS_ENABLED: bool = False
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None

    # CSRF
    CSRF_TOKEN_NAME: str = "csrf_token"
    CSRF_HEADER_NAME: str = "X-CSRF-Token"

    # Cookie settings
    COOKIE_NAME: str = "session"
    COOKIE_PATH: str = "/"
    # In production, set SECURE=True and SAMESITE="lax" or "strict"
    COOKIE_SECURE: bool = False  # Set to True in production
    COOKIE_SAMESITE: str = "lax"  # or "strict"

    @validator("ENVIRONMENT")
    def environment_must_be_valid(cls, v):
        if v not in ("development", "production", "testing"):
            raise ValueError("ENVIRONMENT must be 'development', 'production', or 'testing'")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()