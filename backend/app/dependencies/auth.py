from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import datetime
from app.db.session import get_db
from app.models.user import User
from app.models.session import Session as SessionModel
from app.services.auth_service import hash_token
from app.config import settings

async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current user from the session cookie.
    """
    session_token = request.cookies.get(settings.COOKIE_NAME)
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token_hash = hash_token(session_token)
    db_session = db.query(SessionModel).filter(
        SessionModel.token_hash == token_hash,
        SessionModel.revoked_at == None,  # Not revoked
        SessionModel.expires_at > datetime.datetime.utcnow()  # Not expired
    ).first()
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Update last used at
    db_session.last_used_at = datetime.datetime.utcnow()
    db.commit()
    return db_session.user

async def csrf_protect(
    request: Request
) -> None:
    """
    Dependency to enforce CSRF protection.
    This should be used in addition to the get_current_user dependency for state-changing requests.
    """
    from app.security.csrf import csrf_protection as csrf_dep
    await csrf_dep(request)