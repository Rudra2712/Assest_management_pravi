import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, UUIDPKMixin, TimestampMixin
from app.models.enums import ApprovalStatus, ApprovalEntityType


class Approval(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "approvals"

    entity_type: Mapped[ApprovalEntityType] = mapped_column(nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    submitted_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approver_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    status: Mapped[ApprovalStatus] = mapped_column(nullable=False, default=ApprovalStatus.PENDING)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(nullable=True)
