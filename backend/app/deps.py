"""FastAPI authentication and role-based authorization dependencies."""
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .security import decode_access_token

# Extracts the Bearer token from the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """AUTHENTICATION - who is this user? (valid token, existing, active account)"""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # Decode the JWT and extract the user ID from the subject claim
    try:
        user_id = int(decode_access_token(token)["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise credentials_error

    # Verify the user still exists and is active in the database
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_error
    return user


def require_roles(*allowed: str):
    """AUTHORIZATION - is this user's role allowed to call this endpoint?"""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Your role is not allowed to do this")
        return user

    return checker
