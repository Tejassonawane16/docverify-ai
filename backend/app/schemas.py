from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import Decision, DocStatus, DocType, Role


class RegisterIn(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=200)
    password: str = Field(min_length=10, max_length=128)


class LoginIn(BaseModel):
    email: str = Field(max_length=255)
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: Role
    is_active: bool
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class StaffCreateIn(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=200)
    password: str = Field(min_length=10, max_length=128)
    role: Role


class UserUpdateIn(BaseModel):
    role: Role | None = None
    is_active: bool | None = None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doc_type: DocType
    original_filename: str
    content_type: str
    size_bytes: int
    status: DocStatus
    version: int
    previous_id: int | None
    is_current: bool
    reviewer_comment: str | None
    created_at: datetime
    updated_at: datetime


class StaffDocumentOut(DocumentOut):
    owner_id: int
    owner_name: str
    owner_email: str
    ai_recommendation: str | None
    ai_confidence: float | None


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reviewer_id: int | None
    decision: Decision
    comment: str | None
    ai_recommendation: str | None
    created_at: datetime


class StaffDocumentDetail(StaffDocumentOut):
    ai_report: dict | None
    reviews: list[ReviewOut]
    history: list[DocumentOut]


class ReviewIn(BaseModel):
    decision: Decision
    comment: str | None = Field(default=None, max_length=2000)


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    user_ref: str | None
    action: str
    object_type: str | None
    object_id: str | None
    result: str
    details: str | None


class StatsOut(BaseModel):
    users_by_role: dict[str, int]
    documents_by_status: dict[str, int]
    reviews_total: int
