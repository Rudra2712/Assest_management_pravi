import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, UUIDPKMixin, TimestampMixin


class AuditLog(UUIDPKMixin, TimestampMixin, Base):
    """Immutable business audit trail — separate from application logs, per
    government accountability requirements. Never updated or deleted."""

    __tablename__ = "audit_logs"

    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. ASSET_CREATE, LIFECYCLE_TRANSITION
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    old_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    request_ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    request_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
