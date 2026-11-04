from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import log_action
from app.database import get_db
from app.deps import get_current_user, require_roles
from app.models import DocStatus, DocType, Document, Role, User
from app.schemas import DocumentOut
from app.storage import file_path, save_upload

router = APIRouter(prefix="/api/documents", tags=["documents"])
require_applicant = require_roles(Role.applicant)

REUPLOAD_ALLOWED = {DocStatus.needs_more_info, DocStatus.rejected}


def get_visible_document(doc_id: int, user: User, db: Session) -> Document:
    """Applicants only see their own documents; reviewers and admins see all."""
    doc = db.get(Document, doc_id)
    if doc is None or (user.role == Role.applicant and doc.owner_id != user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    doc_type: DocType = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(require_applicant),
    db: Session = Depends(get_db),
) -> Document:
    """US-04: upload a PDF/JPG/PNG up to 10 MB."""
    stored, content_type, size = await save_upload(file)
    doc = Document(
        owner_id=user.id,
        doc_type=doc_type,
        original_filename=(file.filename or "document")[:255],
        stored_filename=stored,
        content_type=content_type,
        size_bytes=size,
        status=DocStatus.uploaded,
    )
    db.add(doc)
    db.commit()
    log_action(db, "document_upload", user.id, "document", doc.id, details=doc_type.value)
    return doc


@router.get("", response_model=list[DocumentOut])
def list_my_documents(
    include_history: bool = False,
    user: User = Depends(require_applicant),
    db: Session = Depends(get_db),
) -> list[Document]:
    """US-05: the applicant's own documents with their status."""
    query = select(Document).where(Document.owner_id == user.id)
    if not include_history:
        query = query.where(Document.is_current.is_(True))
    return list(db.scalars(query.order_by(Document.created_at.desc())))


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(
    doc_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Document:
    return get_visible_document(doc_id, user, db)


@router.get("/{doc_id}/file")
def download_file(
    doc_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> FileResponse:
    """Files are served only through the API after an access check (never from the web root)."""
    doc = get_visible_document(doc_id, user, db)
    path = file_path(doc.stored_filename)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    log_action(db, "document_download", user.id, "document", doc.id)
    return FileResponse(path, media_type=doc.content_type, filename=doc.original_filename)


@router.post("/{doc_id}/versions", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_new_version(
    doc_id: int,
    file: UploadFile = File(...),
    user: User = Depends(require_applicant),
    db: Session = Depends(get_db),
) -> Document:
    """US-06: upload a corrected version; the old version is kept in the history."""
    old = get_visible_document(doc_id, user, db)
    if not old.is_current:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Not the current version")
    if old.status not in REUPLOAD_ALLOWED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A new version can only be uploaded after a reviewer asked for it",
        )
    stored, content_type, size = await save_upload(file)
    new = Document(
        owner_id=user.id,
        doc_type=old.doc_type,
        original_filename=(file.filename or "document")[:255],
        stored_filename=stored,
        content_type=content_type,
        size_bytes=size,
        status=DocStatus.uploaded,
        version=old.version + 1,
        previous_id=old.id,
    )
    old.is_current = False
    db.add(new)
    db.commit()
    log_action(
        db, "document_new_version", user.id, "document", new.id, details=f"replaces {old.id}"
    )
    return new
