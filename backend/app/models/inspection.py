import uuid
from datetime import date, datetime

from sqlalchemy import ForeignKey, String, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, UUIDPKMixin, TimestampMixin
from app.models.enums import AssetTypeCode, InspectionStatus, FindingSeverity, ConditionRating


class InspectionTemplate(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "inspection_templates"

    asset_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("asset_types.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    items: Mapped[list["InspectionItem"]] = relationship(back_populates="template", cascade="all, delete-orphan")


class InspectionItem(UUIDPKMixin, TimestampMixin, Base):
    """A single checklist question belonging to a template, e.g. 'Pavement cracking?'"""

    __tablename__ = "inspection_items"

    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("inspection_templates.id", ondelete="CASCADE"), nullable=False)
    sequence: Mapped[int] = mapped_column(default=0)
    question: Mapped[str] = mapped_column(String(500), nullable=False)
    response_type: Mapped[str] = mapped_column(String(20), default="RATING")  # RATING | BOOLEAN | TEXT | NUMBER
    weight: Mapped[float] = mapped_column(Numeric(5, 2), default=1.0)

    template: Mapped["InspectionTemplate"] = relationship(back_populates="items")


class Inspection(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "inspections"

    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    template_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("inspection_templates.id"), nullable=True)
    inspector_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    assigned_date: Mapped[date | None] = mapped_column(nullable=True)
    inspection_date: Mapped[date | None] = mapped_column(nullable=True)

    gps_point: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    checklist_responses: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    overall_condition: Mapped[ConditionRating | None] = mapped_column(nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[InspectionStatus] = mapped_column(nullable=False, default=InspectionStatus.ASSIGNED)

    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    review_comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    findings: Mapped[list["InspectionFinding"]] = relationship(back_populates="inspection", cascade="all, delete-orphan")


class InspectionFinding(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "inspection_findings"

    inspection_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[FindingSeverity] = mapped_column(nullable=False, default=FindingSeverity.LOW)
    photo_document_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    recommends_maintenance: Mapped[bool] = mapped_column(default=False)

    inspection: Mapped["Inspection"] = relationship(back_populates="findings")
