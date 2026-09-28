import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import FindingSeverity, GrievanceCategory, GrievanceStatus


class Grievance(UUIDPKMixin, TimestampMixin, Base):
    """A citizen-reportable defect/hazard, optionally pinned to a specific asset and
    a map location (e.g. a damaged bridge railing, a pothole caused by root/water
    damage). Anyone can file one (no auth); only staff can triage and resolve it."""

    __tablename__ = "grievances"

    grievance_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[GrievanceCategory] = mapped_column(nullable=False, default=GrievanceCategory.OTHER)
    severity: Mapped[FindingSeverity] = mapped_column(nullable=False, default=FindingSeverity.LOW)
    status: Mapped[GrievanceStatus] = mapped_column(nullable=False, default=GrievanceStatus.OPEN)

    # GeoJSON Point where the issue was reported; asset_id is optional (the
    # reporter may not know which asset it belongs to — staff can link it later).
    location: Mapped[dict] = mapped_column(JSONB, nullable=False)
    asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True, index=True)
    photo_storage_key: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    reporter_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reporter_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reported_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    linked_maintenance_request_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("maintenance_requests.id"), nullable=True)

    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(nullable=True)

    asset: Mapped["Asset | None"] = relationship()  # noqa: F821
