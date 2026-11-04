from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.audit import log_action
from app.database import get_db
from app.deps import require_staff
from app.models import Decision, DocStatus, Document, ReviewDecision, User
from app.schemas import ReviewIn, StaffDocumentDetail, StaffDocumentOut

router = APIRouter(prefix="/api/review", tags=["review"])

PENDING = [DocStatus.uploaded, DocStatus.processing, DocStatus.in_review]
DECISION_TO_STATUS = {
    Decision.verified: DocStatus.verified,
    Decision.needs_more_info: DocStatus.needs_more_info,
    Decision.rejected: DocStatus.rejected,
}


def _staff_view(doc: Document) -> dict:
    data = {c: getattr(doc, c) for c in StaffDocumentOut.model_fields if hasattr(doc, c)}
    data.update(owner_name=doc.owner.full_name, owner_email=doc.owner.email)
    return data


@router.get("/documents", response_model=list[StaffDocumentOut])
def dashboard(
    status_filter: Literal["pending", "verified", "needs_more_info", "rejected", "all"] = Query(
        "all", alias="status"
    ),
    sort: Literal["date_desc", "date_asc", "confidence_asc", "confidence_desc"] = "date_desc",
    q: str | None = Query(None, max_length=100, description="Search applicant name or email"),
    _: User = Depends(require_staff),
    db: Session = Depends(get_db),
) -> list[dict]:
    """US-13: reviewer dashboard with filters and sorting (current versions only)."""
    query = (
        select(Document)
        .join(Document.owner)
        .options(joinedload(Document.owner))
        .where(Document.is_current.is_(True))
    )
    if status_filter == "pending":
        query = query.where(Document.status.in_(PENDING))
    elif status_filter != "all":
        query = query.where(Document.status == DocStatus(status_filter))
    if q:
        like = f"%{q.lower()}%"
        query = query.where(User.full_name.ilike(like) | User.email.ilike(like))
    order = {
        "date_desc": Document.created_at.desc(),
        "date_asc": Document.created_at.asc(),
        # Documents without an AI score are listed last
        "confidence_asc": Document.ai_confidence.asc().nulls_last(),
        "confidence_desc": Document.ai_confidence.desc().nulls_last(),
    }[sort]
    docs = db.scalars(query.order_by(order, Document.id.desc())).unique()
    return [_staff_view(d) for d in docs]


@router.get("/documents/{doc_id}", response_model=StaffDocumentDetail)
def document_detail(
    doc_id: int, _: User = Depends(require_staff), db: Session = Depends(get_db)
) -> dict:
    """US-14: everything a reviewer needs on one screen."""
    doc = db.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    history = []
    prev = doc.previous_id
    while prev is not None:
        older = db.get(Document, prev)
        if older is None:
            break
        history.append(older)
        prev = older.previous_id
    data = _staff_view(doc)
    data.update(
        ai_report=doc.ai_report,
        reviews=sorted(doc.reviews, key=lambda r: r.created_at, reverse=True),
        history=history,
    )
    return data


@router.post("/documents/{doc_id}/decision", response_model=StaffDocumentOut)
def decide(
    doc_id: int,
    data: ReviewIn,
    reviewer: User = Depends(require_staff),
    db: Session = Depends(get_db),
) -> dict:
    """US-15: the human reviewer makes the final decision."""
    doc = db.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if not doc.is_current:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Not the current version")
    comment = (data.comment or "").strip() or None
    overrides_ai = (
        doc.ai_recommendation is not None and doc.ai_recommendation != data.decision.value
    )
    if comment is None and (data.decision != Decision.verified or overrides_ai):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A comment is required when rejecting, asking for information or overriding the AI",
        )
    db.add(
        ReviewDecision(
            document_id=doc.id,
            reviewer_id=reviewer.id,
            decision=data.decision,
            comment=comment,
            ai_recommendation=doc.ai_recommendation,
        )
    )
    doc.status = DECISION_TO_STATUS[data.decision]
    doc.reviewer_comment = comment
    db.commit()
    log_action(
        db,
        "review_decision",
        reviewer.id,
        "document",
        doc.id,
        details=f"{data.decision.value} (ai: {doc.ai_recommendation or 'none'})",
    )
    return _staff_view(doc)
