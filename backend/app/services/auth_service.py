from sqlalchemy.orm import Session
from app.models.user import User
from app.models.session import Session as SessionModel
from app.models.tokens import EmailVerificationToken, PasswordResetToken
from app.schemas.auth import UserCreate, UserLogin, UserPublic
from app.security.password import get_password_hash, verify_password
from app.security.cookies import set_session_cookie, clear_session_cookie
from app.security.csrf import generate_csrf_token, set_csrf_cookie
import secrets
from datetime import datetime, timedelta
from app.config import settings
import hashlib

def hash_token(token: str) -> str:
    """Hash a token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()

def create_user(db: Session, user_create: UserCreate) -> User:
    """
    Create a new user.
    """
    # Check if user already exists
    db_user = db.query(User).filter(User.email == user_create.email).first()
    if db_user:
        # In a real application, we might want to return a generic error to avoid email enumeration.
        # However, for the purpose of this exercise, we will raise an exception that the API layer can catch and return a generic message.
        # But note: the requirement says "Do not reveal unnecessary account-existence information."
        # So we should not reveal that the email already exists. Instead, we should return a generic success message and then send the email only if the user doesn't exist?
        # However, the requirement for signup says: "Check for an existing account."
        # And then: "Do not reveal unnecessary account-existence information."
        # This is a bit conflicting. We will check for existence, but if it exists, we will not return an error that says the email exists.
        # Instead, we will return a generic message and then send the email only if the user doesn't exist? But then we are not creating the user.
        # Alternatively, we can always return a success message and then send the email only if the user doesn't exist? But then we are not creating the user if it exists.
        # The common practice is to return a generic message (like "If the account doesn't exist, you will receive an email") and then send the email only if the user doesn't exist.
        # However, the requirement for signup is to create the user. So we must create the user only if it doesn't exist.
        # We will do:
        #   If the user exists, we will not create the user and we will return a generic message (without revealing that the user exists).
        #   But note: the requirement says "Create the user." So we are not creating the user if it exists.
        #   This is acceptable because we are not creating a duplicate user.
        #   However, we must also create an email verification token and send the email only if we created the user.
        #   If the user already exists, we will not send the email (to avoid leaking that the email exists) and we will return a generic message.
        #   But wait: what if the user exists but is not verified? We might want to resend the verification email? But the requirement for signup is to create the user and send a verification email.
        #   We are not handling the case where the user exists but is not verified in the signup endpoint.
        #   We have a separate endpoint for resending verification email.
        #   So in the signup endpoint, if the user exists, we will return a generic message and do nothing else (to avoid leaking that the email exists).
        #   This is acceptable because the user can use the forgot password or resend verification endpoints if they need to.
        #
        #   However, note: the requirement says "Check for an existing account." and then "Do not reveal unnecessary account-existence information."
        #   We are checking, and if it exists, we are not creating the user and not sending the email, and returning a generic message.
        #
        #   We will return a message like: "If the account doesn't exist, you will receive an email to verify your address."
        #   But note: we are not actually sending the email if the user exists.
        #
        #   Alternatively, we can always send the email (but with a token that is invalid if the user exists?) but that would be leaking.
        #
        #   Let's stick to: if the user exists, return a generic message and do not create the user or send the email.
        #
        #   We will raise an exception that the API layer can catch and return a generic message.
        #   We'll define a custom exception or just return None and let the API layer handle it.
        #   For now, we'll return None and let the API layer return a generic success message.
        return None

    # Hash the password
    hashed_password = get_password_hash(user_create.password)

    # Create the user
    db_user = User(
        email=user_create.email,
        name=user_create.name,
        hashed_password=hashed_password,
        email_verified=False,  # Initially not verified
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create email verification token
    verification_token = secrets.token_urlsafe(32)
    verification_token_hash = hash_token(verification_token)
    expires_at = datetime.utcnow() + timedelta(minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES)

    db_verification_token = EmailVerificationToken(
        user_id=db_user.id,
        token_hash=verification_token_hash,
        expires_at=expires_at,
    )
    db.add(db_verification_token)
    db.commit()

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

def create_session(db: Session, user_id: int, user_agent: str = None, ip_address: str = None) -> SessionModel:
    """
    Create a new session for the user.
    """
    # Generate a secure random session token
    session_token = secrets.token_urlsafe(32)
    token_hash = hash_token(session_token)

    # Set expiration
    expires_at = datetime.utcnow() + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES)

    # Create the session
    db_session = SessionModel(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    return db_session, session_token

def get_user_from_session(db: Session, session_token: str) -> User:
    """
    Get the user from a session token.
    Returns the user if the session is valid, otherwise None.
    """
    token_hash = hash_token(session_token)
    db_session = db.query(SessionModel).filter(
        SessionModel.token_hash == token_hash,
        SessionModel.revoked_at == None,  # Not revoked
        SessionModel.expires_at > datetime.utcnow()  # Not expired
    ).first()
    if not db_session:
        return None
    return db_session.user

def revoke_session(db: Session, session_token: str) -> bool:
    """
    Revoke a session by setting the revoked_at timestamp.
    Returns True if the session was found and revoked, False otherwise.
    """
    token_hash = hash_token(session_token)
    db_session = db.query(SessionModel).filter(
        SessionModel.token_hash == token_hash,
        SessionModel.revoked_at == None  # Not already revoked
    ).first()
    if db_session:
        db_session.revoked_at = datetime.utcnow()
        db.commit()
        return True
    return False

def revoke_all_sessions_for_user(db: Session, user_id: int) -> int:
    """
    Revoke all sessions for a user.
    Returns the number of sessions revoked.
    """
    # We are not including the current session? We might want to keep the current session.
    # But for security, when changing password, we might want to revoke all sessions.
    # We'll leave it to the caller to decide whether to exclude the current session.
    # For now, we revoke all.
    sessions = db.query(SessionModel).filter(
        SessionModel.user_id == user_id,
        SessionModel.revoked_at == None
    ).all()
    for session in sessions:
        session.revoked_at = datetime.utcnow()
    db.commit()
    return len(sessions)

def get_user_sessions(db: Session, user_id: int):
    """
    Get all active (not revoked, not expired) sessions for a user.
    """
    return db.query(SessionModel).filter(
        SessionModel.user_id == user_id,
        SessionModel.revoked_at == None,
        SessionModel.expires_at > datetime.utcnow()
    ).order_by(SessionModel.created_at.desc()).all()

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