"""Private file storage for uploaded documents (US-04)."""

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.config import get_settings

ALLOWED = {
    ".pdf": ("application/pdf", [b"%PDF"]),
    ".png": ("image/png", [b"\x89PNG\r\n\x1a\n"]),
    ".jpg": ("image/jpeg", [b"\xff\xd8\xff"]),
    ".jpeg": ("image/jpeg", [b"\xff\xd8\xff"]),
}


def upload_dir() -> Path:
    path = Path(get_settings().upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


async def save_upload(file: UploadFile) -> tuple[str, str, int]:
    """Validate type (extension and file signature) and size, then save under a random name.

    Returns (stored_filename, content_type, size_bytes).
    """
    max_bytes = get_settings().max_upload_mb * 1024 * 1024
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF, JPG and PNG files are allowed",
        )
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File is larger than {get_settings().max_upload_mb} MB",
        )
    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")
    content_type, signatures = ALLOWED[ext]
    if not any(content.startswith(sig) for sig in signatures):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File content does not match its type",
        )
    stored = f"{uuid.uuid4().hex}{ext}"
    (upload_dir() / stored).write_bytes(content)
    return stored, content_type, len(content)


def file_path(stored_filename: str) -> Path:
    return upload_dir() / stored_filename
