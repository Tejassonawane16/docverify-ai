from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import log_action
from app.config import get_settings
from app.database import get_db
from app.deps import get_current_user, get_token_payload
from app.models import RevokedToken, Role, User
from app.schemas import LoginIn, RegisterIn, TokenOut, UserOut
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

INVALID_LOGIN = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
)


def _aware(dt: datetime | None) -> datetime | None:
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(data: RegisterIn, db: Session = Depends(get_db)) -> TokenOut:
    """US-01: applicants create their own account."""
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        log_action(db, "register", object_type="user", result="failure", details="email exists")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(
        email=email,
        full_name=data.full_name.strip(),
        password_hash=hash_password(data.password),
        role=Role.applicant,
    )
    db.add(user)
    db.commit()
    log_action(db, "register", user.id, "user", user.id)
    return TokenOut(
        access_token=create_access_token(user.id, user.role.value),
        user=UserOut.model_validate(user),
    )


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    """US-02: login with a generic error and a lockout after repeated failures."""
    settings = get_settings()
    now = datetime.now(UTC)
    user = db.scalar(select(User).where(User.email == data.email.lower()))

    if user is None:
        log_action(db, "login", None, "user", None, "failure", "unknown email")
        raise INVALID_LOGIN

    locked_until = _aware(user.locked_until)
    if locked_until is not None and now < locked_until:
        log_action(db, "login", user.id, "user", user.id, "blocked", "account locked")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts. Try again later.",
        )

    if not user.is_active or not verify_password(data.password, user.password_hash):
        window = timedelta(minutes=settings.lockout_minutes)
        first = _aware(user.first_failed_at)
        if first is None or now - first > window:
            user.failed_logins, user.first_failed_at = 1, now
        else:
            user.failed_logins += 1
        if user.failed_logins >= settings.max_failed_logins:
            user.locked_until = now + window
        db.commit()
        log_action(db, "login", user.id, "user", user.id, "failure", "wrong password or inactive")
        raise INVALID_LOGIN

    user.failed_logins, user.first_failed_at, user.locked_until = 0, None, None
    db.commit()
    log_action(db, "login", user.id, "user", user.id)
    return TokenOut(
        access_token=create_access_token(user.id, user.role.value),
        user=UserOut.model_validate(user),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: dict = Depends(get_token_payload),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """US-02: the token is put on a deny list and can no longer be used."""
    db.add(RevokedToken(jti=payload["jti"], expires_at=datetime.fromtimestamp(payload["exp"], UTC)))
    db.commit()
    log_action(db, "logout", user.id, "user", user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    """US-21: applicants delete their account, documents and files (GDPR right to erasure)."""
    if user.role != Role.applicant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Staff accounts are removed by an admin"
        )
    upload_dir = Path(get_settings().upload_dir)
    for doc in user.documents:
        (upload_dir / doc.stored_filename).unlink(missing_ok=True)
    user_id = user.id
    db.delete(user)
    db.commit()
    log_action(db, "account_deleted", user_id, "user", user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
