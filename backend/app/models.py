import enum
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Role(str, enum.Enum):
    applicant = "applicant"
    reviewer = "reviewer"
    admin = "admin"


class DocType(str, enum.Enum):
    degree_certificate = "degree_certificate"
    transcript = "transcript"
    language_certificate = "language_certificate"
    id_document = "id_document"
    other = "other"


class DocStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    in_review = "in_review"
    verified = "verified"
    needs_more_info = "needs_more_info"
    rejected = "rejected"


class Decision(str, enum.Enum):
    verified = "verified"
    needs_more_info = "needs_more_info"
    rejected = "rejected"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role, native_enum=False), default=Role.applicant)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    failed_logins: Mapped[int] = mapped_column(Integer, default=0)
    first_failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    documents: Mapped[list["Document"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    doc_type: Mapped[DocType] = mapped_column(Enum(DocType, native_enum=False))
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(255), unique=True)
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    status: Mapped[DocStatus] = mapped_column(
        Enum(DocStatus, native_enum=False), default=DocStatus.uploaded, index=True
    )

    # Version history (US-06)
    version: Mapped[int] = mapped_column(Integer, default=1)
    previous_id: Mapped[int | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # Comment from the reviewer that the applicant can see (US-06)
    reviewer_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Filled by the AI service in Phase 3 (US-09, US-10)
    ai_recommendation: Mapped[str | None] = mapped_column(String(30), nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_report: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    owner: Mapped[User] = relationship(back_populates="documents")
    reviews: Mapped[list["ReviewDecision"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    reviewer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decision: Mapped[Decision] = mapped_column(Enum(Decision, native_enum=False))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_recommendation: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    document: Mapped[Document] = relationship(back_populates="reviews")


class AuditLog(Base):
    """Append-only audit trail (US-19). No foreign key, so entries survive account deletion."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    user_ref: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(50), index=True)
    object_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    object_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    result: Mapped[str] = mapped_column(String(20), default="success")
    details: Mapped[str | None] = mapped_column(Text, nullable=True)


class RevokedToken(Base):
    """Tokens invalidated by logout (US-02)."""

    __tablename__ = "revoked_tokens"

    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
