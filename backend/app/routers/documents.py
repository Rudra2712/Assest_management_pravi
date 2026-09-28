from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.document import Document, DocumentVersion
from app.models.enums import DocumentType
from app.models.user import User
from app.schemas.document import DocumentRead
from app.utils import storage
from app.utils.audit import record_audit

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentRead])
def list_documents(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
    linked_entity_type: str | None = None,
    linked_entity_id: UUID | None = None,
):
    query = db.query(Document)
    if linked_entity_type:
        query = query.filter(Document.linked_entity_type == linked_entity_type)
    if linked_entity_id:
        query = query.filter(Document.linked_entity_id == linked_entity_id)
    return query.order_by(Document.created_at.desc()).all()


@router.post("", response_model=DocumentRead, status_code=201)
async def upload_document(
    document_type: DocumentType = Form(...),
    linked_entity_type: str = Form(...),
    linked_entity_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = await file.read()
    try:
        storage.validate_upload(file, len(content))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    storage_key = storage.build_storage_key(linked_entity_type, file.filename or "upload")
    storage.save_file(storage_key, content)

    document = Document(
        document_type=document_type,
        filename=file.filename or "upload",
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=len(content),
        storage_key=storage_key,
        linked_entity_type=linked_entity_type,
        linked_entity_id=linked_entity_id,
        uploaded_by=user.id,
        current_version=1,
    )
    db.add(document)
    db.flush()
    db.add(DocumentVersion(document_id=document.id, version_number=1, storage_key=storage_key, size_bytes=len(content), uploaded_by=user.id))

    record_audit(db, actor_id=user.id, action="DOCUMENT_UPLOAD", entity_type="document", entity_id=document.id, new_value={"filename": document.filename, "linked_entity_type": linked_entity_type})
    db.commit()
    db.refresh(document)
    return document


@router.post("/{document_id}/versions", response_model=DocumentRead)
async def upload_new_version(
    document_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    content = await file.read()
    try:
        storage.validate_upload(file, len(content))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    storage_key = storage.build_storage_key(document.linked_entity_type, file.filename or "upload")
    storage.save_file(storage_key, content)

    document.current_version += 1
    document.storage_key = storage_key
    document.size_bytes = len(content)
    document.filename = file.filename or document.filename

    db.add(DocumentVersion(document_id=document.id, version_number=document.current_version, storage_key=storage_key, size_bytes=len(content), uploaded_by=user.id))
    record_audit(db, actor_id=user.id, action="DOCUMENT_VERSION_UPLOAD", entity_type="document", entity_id=document.id, new_value={"version": document.current_version})
    db.commit()
    db.refresh(document)
    return document


@router.get("/{document_id}/download")
def download_document(document_id: UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    path = storage.resolve_path(document.storage_key)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File missing from storage")
    return FileResponse(path, media_type=document.mime_type, filename=document.filename)


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    for version in document.versions:
        storage.delete_file(version.storage_key)
    record_audit(db, actor_id=user.id, action="DOCUMENT_DELETE", entity_type="document", entity_id=document.id, old_value={"filename": document.filename})
    db.delete(document)
    db.commit()
