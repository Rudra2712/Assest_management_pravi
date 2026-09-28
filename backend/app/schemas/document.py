from datetime import datetime
from uuid import UUID

from app.models.enums import DocumentType
from app.schemas.common import ORMModel


class DocumentRead(ORMModel):
    id: UUID
    document_type: DocumentType
    filename: str
    mime_type: str
    size_bytes: int
    linked_entity_type: str
    linked_entity_id: UUID
    uploaded_by: UUID
    current_version: int
    created_at: datetime
