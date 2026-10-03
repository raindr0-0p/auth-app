from sqlalchemy.orm import Session
from app.models.user import User
from app.models.tokens import EmailVerificationToken, PasswordResetToken
from app.schemas.auth import UserCreate, UserLogin, UserPublic
from app.security.password import get_password_hash, verify_password
from app.security.cookies import set_session_cookie, clear_session_cookie
from app.security.csrf import generate_csrf_token, set_csrf_cookie
from app.services import session_service
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from app.config import settings

def hash_token(token: str) -> str:
    """Hash a token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()

def create_user(db: Session, user_create: UserCreate) -> User:
    """
    Create a new user.
    """
    # Normalize email (lowercase)
    normalized_email = user_create.email.lower()

    # Check if user already exists with normalized email
    db_user = db.query(User).filter(User.email == normalized_email).first()
    if db_user:
        # User already exists, return None to avoid revealing account existence
        # The API layer will handle returning a generic message
        return None

    # Hash the password
    hashed_password = get_password_hash(user_create.password)

    # Create the user with normalized email
    db_user = User(
        email=normalized_email,
        name=user_create.name,
        hashed_password=hashed_password,
        email_verified=False,  # Initially not verified
    )
    db.add(db_user)
    # Don't commit yet - wait for token creation

    # Create email verification token
    verification_token = secrets.token_urlsafe(32)
    verification_token_hash = hash_token(verification_token)
    expires_at = datetime.utcnow() + timedelta(minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES)

    db_verification_token = EmailVerificationToken(
        user_id=db_user.id,  # This will work after flush
        token_hash=verification_token_hash,
        expires_at=expires_at,
    )
    db.add(db_verification_token)

    # Commit both user and token in a single transaction
    db.commit()
    db.refresh(db_user)
    db.refresh(db_verification_token)

    # In a real application, we would send the email here.
    # For development, we will print the token to the console.
    print(f"Email verification token for {db_user.email}: {verification_token}")

    return db_user

def authenticate_user(db: Session, email: str, password: str) -> User:
    """
    Authenticate a user by email and password.
    Returns the user if authentication is successful, otherwise None.
    """
    # Normalize email (lowercase)
    email = email.lower()
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        # User not found, but we return None to avoid leaking that the email exists.
        return None
    if not verify_password(password, db_user.hashed_password):
        # Password incorrect, return None to avoid leaking that the email exists.
        return None
    return db_user

def create_session(db: Session, user_id: int, user_agent: str = None, ip_address: str = None) -> tuple:
    """
    Create a new session for the user.
    Returns (session_model, session_token)
    """
    # Use session service
    db_session = session_service.create_session(db, user_id, user_agent, ip_address)

    # Generate the session token to return (the service doesn't return it)
    import secrets
    session_token = secrets.token_urlsafe(32)

    return db_session, session_token

def get_user_from_session(db: Session, session_token: str) -> User:
    """
    Get the user from a session token.
    Returns the user if the session is valid, otherwise None.
    """
    db_session = session_service.get_session(db, session_token)
    if not db_session:
        return None
    return db_session.user

def revoke_session(db: Session, session_token: str) -> bool:
    """
    Revoke a session by setting the revoked_at timestamp.
    Returns True if the session was found and revoked, False otherwise.
    """
    return session_service.revoke_session(db, session_token)

def revoke_all_sessions_for_user(db: Session, user_id: int, exclude_session_id: Optional[int] = None) -> int:
    """
    Revoke all sessions for a user.
    Optionally exclude a specific session (e.g., the current one).
    Returns the number of sessions revoked.
    """
    return session_service.revoke_all_sessions_for_user(db, user_id, exclude_session_id)

def get_user_sessions(db: Session, user_id: int):
    """
    Get all active (not revoked, not expired) sessions for a user.
    """
    return session_service.get_user_sessions(db, user_id)

def verify_email_token(db: Session, token: str) -> bool:
    """
    Verify an email verification token.
    Returns True if the token is valid and marks it as used, False otherwise.
    """
    token_hash = hash_token(token)
    db_token = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.token_hash == token_hash,
        EmailVerificationToken.used_at == None,  # Not used
        EmailVerificationToken.expires_at > datetime.utcnow()  # Not expired
    ).first()
    if not db_token:
        return False
    # Mark as used
    db_token.used_at = datetime.utcnow()
    # Mark the user's email as verified
    user = db_token.user
    user.email_verified = True
    db.commit()
    return True

def create_password_reset_token(db: Session, user_id: int) -> str:
    """
    Create a password reset token for the user.
    Returns the plain token (only shown once).
    """
    # Check if there is an existing unused token? We could invalidate it, but let's just create a new one.
    # We are not storing the plain token, only the hash.
    reset_token = secrets.token_urlsafe(32)
    token_hash = hash_token(reset_token)
    expires_at = datetime.utcnow() + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)

    db_token = PasswordResetToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(db_token)
    db.commit()

    return reset_token

def verify_password_reset_token(db: Session, token: str) -> bool:
    """
    Verify a password reset token.
    Returns True if the token is valid, False otherwise.
    Note: we do not mark it as used here; that is done in the reset password function.
    """
    token_hash = hash_token(token)
    db_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used_at == None,  # Not used
        PasswordResetToken.expires_at > datetime.utcnow()  # Not expired
    ).first()
    return db_token is not None

def use_password_reset_token(db: Session, token: str) -> bool:
    """
    Mark a password reset token as used.
    Returns True if the token was found and marked as used, False otherwise.
    """
    token_hash = hash_token(token)
    db_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used_at == None  # Not used
    ).first()
    if db_token:
        db_token.used_at = datetime.utcnow()
        db.commit()
        return True
    return False

def reset_password(db: Session, token: str, new_password: str) -> bool:
    """
    Reset the password using a token.
    Returns True if successful, False otherwise.
    """
    # Verify the token is valid and not used
    if not verify_password_reset_token(db, token):
        return False
    # Hash the new password
    hashed_password = get_password_hash(new_password)
    # Find the token to get the user
    token_hash = hash_token(token)
    db_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used_at == None
    ).first()
    if not db_token:
        return False
    # Update the user's password
    user = db_token.user
    user.hashed_password = hashed_password
    # Mark the token as used
    db_token.used_at = datetime.utcnow()
    # Revoke all existing sessions for the user (except the current one? We don't have the current session token here)
    # We are going to revoke all sessions for security.
    revoke_all_sessions_for_user(db, user.id)
    db.commit()
    return True

def change_password(db: Session, user_id: int, current_password: str, new_password: str) -> bool:
    """
    Change the password for a user.
    Returns True if successful, False otherwise.
    """
    # Get the user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    # Verify the current password
    if not verify_password(current_password, user.hashed_password):
        return False
    # Hash the new password
    hashed_password = get_password_hash(new_password)
    # Update the password
    user.hashed_password = hashed_password
    # Revoke all existing sessions for the user (except the current one? We don't have the current session token here)
    # We are going to revoke all sessions for security.
    revoke_all_sessions_for_user(db, user.id)
    db.commit()
    return True