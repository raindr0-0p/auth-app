from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from typing import List
from app.models.user import User
from app.schemas.auth import (
    UserCreate, UserLogin, UserPublic, TokenBase,
    EmailVerificationRequest, PasswordResetRequest,
    ResendVerificationRequest, ForgotPasswordRequest,
    Message, SessionInfo, SessionList, ChangePasswordRequest
)
from app.services.auth_service import (
    create_user, authenticate_user, create_session,
    revoke_session, revoke_all_sessions_for_user,
    verify_email_token, create_password_reset_token,
    verify_password_reset_token, use_password_reset_token,
    reset_password, change_password, get_user_from_session,
    get_user_sessions
)
from app.services.email_service import email_service
from app.services.session_service import update_session_last_used
from app.db.session import get_db
from app.dependencies.auth import get_current_user, csrf_protect
from app.security.rati_limit import (
    login_rate_limit, signup_rate_limit,
    forgot_password_rate_limit, resend_verification_rate_limit
)
from app.config import settings
import secrets
from datetime import datetime, timedelta

router = APIRouter()

@router.post("/signup", response_model=Message)
async def signup(
    request: Request,
    response: Response,
    user_create: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new user account.
    """
    # Apply rate limiting
    signup_rate_limit(request)

    # Create the user
    db_user = create_user(db, user_create)
    if db_user is None:
        # User already exists - return generic message to avoid email enumeration
        return Message(detail="If the account doesn't exist, you will receive an email to verify your address.")

    # Note: The actual email sending is handled in the create_user function (logging in dev)
    # In a real application, we would send the email here or in a background task.

    return Message(detail="If the account doesn't exist, you will receive an email to verify your address.")

@router.post("/login", response_model=UserPublic)
async def login(
    request: Request,
    response: Response,
    user_login: UserLogin,
    db: Session = Depends(get_db),
    _: None = Depends(csrf_protect)
):
    """
    Log in a user and create a session.
    """
    # Apply rate limiting
    login_rate_limit(request)

    # Authenticate the user
    user = authenticate_user(db, user_login.email, user_login.password)
    if not user:
        # Generic error to avoid leaking whether the email exists
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if email is verified
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please verify your email before logging in",
        )

    # Create session
    db_session, session_token = create_session(
        db,
        user.id,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None
    )

    # Set session cookie
    set_session_cookie(response, session_token)

    # Generate and set CSRF token
    csrf_token = generate_csrf_token()
    set_csrf_cookie(response, csrf_token)

    # Return user info
    return UserPublic(
        id=user.id,
        email=user.email,
        name=user.name,
        email_verified=user.email_verified,
        is_active=user.is_active,
        created_at=user.created_at
    )

@router.get("/me", response_model=UserPublic)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Get the current authenticated user's information.
    """
    # Update session last used time
    session_token = request.cookies.get(settings.COOKIE_NAME)
    if session_token:
        token_hash = hash_token(session_token)
        db_session = db.query(SessionModel).filter(
            SessionModel.token_hash == token_hash
        ).first()
        if db_session:
            db_session.last_used_at = datetime.utcnow()
            db.commit()

    return UserPublic(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        email_verified=current_user.email_verified,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )

@router.post("/logout", response_model=Message)
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(csrf_protect)
):
    """
    Log out the current user by revoking their session.
    """
    session_token = request.cookies.get(settings.COOKIE_NAME)
    if session_token:
        revoke_session(db, session_token)
        clear_session_cookie(response)
        clear_csrf_cookie(response)

    return Message(detail="Successfully logged out")

@router.post("/verify-email", response_model=Message)
async def verify_email(
    request: Request,
    token_request: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Verify an email address using a token.
    """
    token = token_request.token
    if verify_email_token(db, token):
        return Message(detail="Email verified successfully")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

@router.post("/resend-verification", response_model=Message)
async def resend_verification(
    request: Request,
    resend_request: ResendVerificationRequest,
    db: Session = Depends(get_db),
    _: None = Depends(csrf_protect)
):
    """
    Resend the email verification email.
    """
    # Apply rate limiting
    resend_verification_rate_limit(request)

    # Normalize email
    email = resend_request.email.lower()

    # Find user by normalized email (to avoid enumeration)
    user = db.query(User).filter(User.email == email).first()

    # Always return generic response to avoid account enumeration
    if user and not user.email_verified:
        # Generate a fresh verification token
        verification_token = secrets.token_urlsafe(32)
        verification_token_hash = hash_token(verification_token)
        expires_at = datetime.utcnow() + timedelta(minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES)

        # Invalidate any existing unused verification tokens for this user
        existing_tokens = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.used_at == None
        ).all()
        for token in existing_tokens:
            token.used_at = datetime.utcnow()  # Mark as used

        # Create new verification token
        db_verification_token = EmailVerificationToken(
            user_id=user.id,
            token_hash=verification_token_hash,
            expires_at=expires_at,
        )
        db.add(db_verification_token)
        db.commit()

        # In a real application, we would send the email here.
        # For development, we will print the token to the console.
        print(f"Email verification token for {user.email}: {verification_token}")

    return Message(detail="If the account exists and is not verified, you will receive a verification email.")

@router.post("/forgot-password", response_model=Message)
async def forgot_password(
    request: Request,
    forgot_request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
    _: None = Depends(csrf_protect)
):
    """
    Request a password reset email.
    """
    # Apply rate limiting
    forgot_password_rate_limit(request)

    # Normalize email
    email = forgot_request.email.lower()

    # Find user by normalized email (to avoid enumeration)
    user = db.query(User).filter(User.email == email).first()

    # Always return generic response to avoid account enumeration
    if user and user.is_active:
        # Generate a password reset token
        reset_token = create_password_reset_token(db, user.id)

        # In a real application, we would send the email here.
        # For development, we will print the reset link to the console.
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        print(f"Password reset URL for {user.email}: {reset_url}")

    return Message(detail="If the account exists, you will receive a password reset email.")

@router.post("/reset-password", response_model=Message)
async def reset_password_endpoint(
    request: Request,
    password_reset: PasswordResetRequest,
    db: Session = Depends(get_db),
    _: None = Depends(csrf_protect)
):
    """
    Reset password using a token.
    """
    token = password_reset.token
    new_password = password_reset.new_password

    if reset_password(db, token, new_password):
        return Message(detail="Password has been reset successfully")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

@router.post("/change-password", response_model=Message)
async def change_password_endpoint(
    change_password: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(csrf_protect)
):
    """
    Change the current user's password.
    """
    current_password = change_password.current_password
    new_password = change_password.new_password

    if change_password(db, current_user.id, current_password, new_password):
        return Message(detail="Password changed successfully")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

# Additional endpoints for session management
@router.get("/sessions", response_model=SessionList)
async def get_user_sessions_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all active sessions for the current user.
    """
    sessions = get_user_sessions(db, current_user.id)
    return SessionList(sessions=[
        SessionInfo(
            id=session.id,
            created_at=session.created_at,
            expires_at=session.expires_at,
            last_used_at=session.last_used_at,
            user_agent=session.user_agent,
            ip_address=session.ip_address
        ) for session in sessions
    ])

@router.delete("/sessions/{session_id}", response_model=Message)
async def revoke_session_endpoint(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(csrf_protect)
):
    """
    Revoke a specific session for the current user.
    """
    # Verify the session belongs to the current user
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Revoke the session by setting revoked_at timestamp
    session.revoked_at = datetime.utcnow()
    db.commit()

    return Message(detail="Session revoked successfully")

@router.post("/sessions/revoke-others", response_model=Message)
async def revoke_other_sessions_endpoint(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(csrf_protect)
):
    """
    Revoke all other sessions for the current user (keep the current one).
    """
    # Get current session token from cookie
    session_token = request.cookies.get(settings.COOKIE_NAME)
    if not session_token:
        # If no session token, revoke all sessions (edge case)
        count = revoke_all_sessions_for_user(db, current_user.id)
        return Message(detail=f"Revoked {count} sessions")

    # Hash the token to find the session in DB
    token_hash = hash_token(session_token)
    current_session = db.query(SessionModel).filter(
        SessionModel.token_hash == token_hash,
        SessionModel.user_id == current_user.id,
        SessionModel.revoked_at == None
    ).first()

    if not current_session:
        # If current session not found, revoke all sessions
        count = revoke_all_sessions_for_user(db, current_user.id)
        return Message(detail=f"Revoked {count} sessions")

    # Get all sessions for the user
    all_sessions = db.query(SessionModel).filter(
        SessionModel.user_id == current_user.id,
        SessionModel.revoked_at == None
    ).all()

    # Revoke all except the current session
    revoked_count = 0
    for session in all_sessions:
        if session.id != current_session.id:
            session.revoked_at = datetime.utcnow()
            revoked_count += 1

    db.commit()
    return Message(detail=f"Revoked {revoked_count} other sessions")

# Helper functions that need to be imported or defined
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

def hash_token(token: str) -> str:
    """Hash a token for storage."""
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()

# Import SessionModel to avoid circular imports
from app.models.session import Session as SessionModel