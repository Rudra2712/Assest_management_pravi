import uuid

from sqlalchemy import ForeignKey, String, Integer, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, UUIDPKMixin, TimestampMixin
from app.models.enums import DocumentType


class Document(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    document_type: Mapped[DocumentType] = mapped_column(nullable=False)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(150), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1000), nullable=False)

    # Polymorphic link: which entity this document belongs to (asset, inspection, work_order, project, ...)
    linked_entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    linked_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    access_roles: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    current_version: Mapped[int] = mapped_column(Integer, default=1)

    versions: Mapped[list["DocumentVersion"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocumentVersion(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "document_versions"

    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1000), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    document: Mapped["Document"] = relationship(back_populates="versions")
