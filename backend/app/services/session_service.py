"""
Session service for managing user sessions.
This file contains session-related business logic.
"""
from sqlalchemy.orm import Session
from app.models.session import Session as SessionModel
from app.models.user import User
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import secrets
import hashlib
from app.config import settings

def hash_token(token: str) -> str:
    """Hash a token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()

def create_session(db: Session, user_id: int, user_agent: str = None, ip_address: str = None) -> Tuple[SessionModel, str]:
    """
    Create a new session for the user.
    Returns (session_model, session_token)
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

def get_session(db: Session, session_token: str) -> Optional[SessionModel]:
    """
    Get a session by token.
    Returns the session if valid and not expired/revoked, otherwise None.
    """
    token_hash = hash_token(session_token)
    return db.query(SessionModel).filter(
        SessionModel.token_hash == token_hash,
        SessionModel.revoked_at == None,  # Not revoked
        SessionModel.expires_at > datetime.utcnow()  # Not expired
    ).first()

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

def revoke_all_sessions_for_user(db: Session, user_id: int, exclude_session_id: Optional[int] = None) -> int:
    """
    Revoke all sessions for a user.
    Optionally exclude a specific session (e.g., the current one).
    Returns the number of sessions revoked.
    """
    query = db.query(SessionModel).filter(
        SessionModel.user_id == user_id,
        SessionModel.revoked_at == None
    )
    if exclude_session_id:
        query = query.filter(SessionModel.id != exclude_session_id)

    sessions = query.all()
    for session in sessions:
        session.revoked_at = datetime.utcnow()
    db.commit()
    return len(sessions)

def get_user_sessions(db: Session, user_id: int) -> List[SessionModel]:
    """
    Get all active (not revoked, not expired) sessions for a user.
    """
    return db.query(SessionModel).filter(
        SessionModel.user_id == user_id,
        SessionModel.revoked_at == None,
        SessionModel.expires_at > datetime.utcnow()
    ).order_by(SessionModel.created_at.desc()).all()

def update_session_last_used(db: Session, session_token: str) -> bool:
    """
    Update the last_used_at timestamp for a session.
    Returns True if the session was found and updated, False otherwise.
    """
    db_session = get_session(db, session_token)
    if db_session:
        db_session.last_used_at = datetime.utcnow()
        db.commit()
        return True
    return False