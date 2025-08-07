from typing import Optional
from fastapi import Depends, HTTPException, status, Cookie, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_token
from app.crud.crud import get_user
from app.models.models import User

security = HTTPBearer()


def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token"""
    token = credentials.credentials
    username = verify_token(token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_user_by_username(db, username=username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_current_user_from_cookie(
    request: Request,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None)
) -> Optional[User]:
    """Get current user from cookie (for web pages)"""
    if not access_token:
        return None
    
    username = verify_token(access_token)
    if username is None:
        return None
    
    from app.crud.crud import get_user_by_username
    user = get_user_by_username(db, username=username)
    return user


def require_auth(
    request: Request,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None)
) -> User:
    """Require authentication for web pages"""
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    username = verify_token(access_token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    from app.crud.crud import get_user_by_username
    user = get_user_by_username(db, username=username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user
