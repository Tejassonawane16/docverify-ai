from sqlalchemy.orm import Session

from app.models import AuditLog


def user_ref(user_id: int | None) -> str | None:
    """Pseudonymous user reference stored in the audit log (keeps entries after deletion)."""
    return f"user-{user_id}" if user_id is not None else None


def log_action(
    db: Session,
    action: str,
    user_id: int | None = None,
    object_type: str | None = None,
    object_id: int | str | None = None,
    result: str = "success",
    details: str | None = None,
    commit: bool = True,
) -> None:
    db.add(
        AuditLog(
            user_ref=user_ref(user_id),
            action=action,
            object_type=object_type,
            object_id=str(object_id) if object_id is not None else None,
            result=result,
            details=details,
        )
    )
    if commit:
        db.commit()
