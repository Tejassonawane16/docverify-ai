from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit import log_action
from app.database import get_db
from app.deps import require_admin
from app.models import AuditLog, Document, ReviewDecision, Role, User
from app.schemas import AuditOut, StaffCreateIn, StatsOut, UserOut, UserUpdateIn
from app.security import hash_password

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
def list_users(
    role: Role | None = None, _: User = Depends(require_admin), db: Session = Depends(get_db)
) -> list[User]:
    query = select(User).order_by(User.created_at.desc())
    if role is not None:
        query = query.where(User.role == role)
    return list(db.scalars(query))


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    data: StaffCreateIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)
) -> User:
    """US-03: admins create staff accounts with a role."""
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(
        email=email,
        full_name=data.full_name.strip(),
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    db.commit()
    log_action(db, "user_created", admin.id, "user", user.id, details=f"role={data.role.value}")
    return user


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: UserUpdateIn,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    """US-03: change role or deactivate; takes effect on the user's next request."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot change your own account"
        )
    changes = []
    if data.role is not None and data.role != user.role:
        changes.append(f"role {user.role.value}->{data.role.value}")
        user.role = data.role
    if data.is_active is not None and data.is_active != user.is_active:
        changes.append(f"active {user.is_active}->{data.is_active}")
        user.is_active = data.is_active
    db.commit()
    if changes:
        log_action(db, "user_updated", admin.id, "user", user.id, details=", ".join(changes))
    return user


@router.get("/audit", response_model=list[AuditOut])
def audit_log(
    user_ref: str | None = None,
    action: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(200, ge=1, le=1000),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[AuditLog]:
    """US-19: read-only audit log with filters. There is no endpoint to edit or delete entries."""
    query = select(AuditLog)
    if user_ref:
        query = query.where(AuditLog.user_ref == user_ref)
    if action:
        query = query.where(AuditLog.action == action)
    if date_from:
        query = query.where(AuditLog.timestamp >= date_from)
    if date_to:
        query = query.where(AuditLog.timestamp <= date_to)
    return list(db.scalars(query.order_by(AuditLog.id.desc()).limit(limit)))


@router.get("/stats", response_model=StatsOut)
def stats(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> StatsOut:
    users = db.execute(select(User.role, func.count()).group_by(User.role)).all()
    docs = db.execute(
        select(Document.status, func.count())
        .where(Document.is_current.is_(True))
        .group_by(Document.status)
    ).all()
    return StatsOut(
        users_by_role={r.value: n for r, n in users},
        documents_by_status={s.value: n for s, n in docs},
        reviews_total=db.scalar(select(func.count()).select_from(ReviewDecision)) or 0,
    )
