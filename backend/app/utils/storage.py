"""Local-filesystem document storage for the hackathon MVP.

Every call goes through this module rather than touching the filesystem
directly from routers/services, so swapping in S3/MinIO later only requires
reimplementing these three functions.
"""

import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import settings

ALLOWED_LINKED_ENTITY_FOLDERS = {
    "asset": "assets",
    "inspection": "inspections",
    "maintenance_request": "maintenance",
    "work_order": "maintenance",
    "project": "projects",
    "grievance": "grievances",
}
DEFAULT_FOLDER = "documents"


def _folder_for(linked_entity_type: str) -> str:
    return ALLOWED_LINKED_ENTITY_FOLDERS.get(linked_entity_type, DEFAULT_FOLDER)


def validate_upload(file: UploadFile, size_bytes: int) -> None:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        raise ValueError(f"File type '{ext}' is not allowed")
    if size_bytes > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise ValueError(f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")


def build_storage_key(linked_entity_type: str, original_filename: str) -> str:
    ext = Path(original_filename).suffix.lower()
    folder = _folder_for(linked_entity_type)
    return f"{folder}/{uuid.uuid4()}{ext}"


def save_file(storage_key: str, content: bytes) -> None:
    path = settings.UPLOAD_DIR / storage_key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def read_file(storage_key: str) -> bytes:
    path = settings.UPLOAD_DIR / storage_key
    if not path.exists():
        raise FileNotFoundError(storage_key)
    return path.read_bytes()


def delete_file(storage_key: str) -> None:
    path = settings.UPLOAD_DIR / storage_key
    if path.exists():
        path.unlink()


def resolve_path(storage_key: str) -> Path:
    return settings.UPLOAD_DIR / storage_key
