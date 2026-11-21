from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RevokedToken, Role, User
from app.security import decode_access_token

bearer = HTTPBearer(auto_error=False)

UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_token_payload(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> dict:
    if creds is None:
        raise UNAUTHORIZED
    try:
        payload = decode_access_token(creds.credentials)
    except jwt.PyJWTError as exc:
        raise UNAUTHORIZED from exc
    if db.get(RevokedToken, payload.get("jti", "")) is not None:
        raise UNAUTHORIZED
    return payload


def get_current_user(
    payload: dict = Depends(get_token_payload), db: Session = Depends(get_db)
) -> User:
    # The role is always read from the database, so role changes apply on the next request (US-03).
    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise UNAUTHORIZED
    return user


def require_roles(*roles: Role) -> Callable[[User], User]:
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
        return user

    return checker


require_staff = require_roles(Role.reviewer, Role.admin)
require_admin = require_roles(Role.admin)
