import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, UUIDPKMixin, TimestampMixin
from app.models.enums import LifecycleStatus


class LifecycleEvent(UUIDPKMixin, TimestampMixin, Base):
    """Append-only lifecycle transition log. Never updated or deleted once written."""

    __tablename__ = "lifecycle_events"

    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    old_status: Mapped[LifecycleStatus | None] = mapped_column(nullable=True)
    new_status: Mapped[LifecycleStatus] = mapped_column(nullable=False)
    changed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    approval_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("approvals.id"), nullable=True)

    asset: Mapped["Asset"] = relationship()  # noqa: F821
