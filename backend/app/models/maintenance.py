import uuid
from datetime import date

from sqlalchemy import ForeignKey, String, Text, Numeric, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, UUIDPKMixin, TimestampMixin
from app.models.enums import (
    MaintenanceType,
    MaintenancePriority,
    MaintenanceRequestStatus,
    WorkOrderStatus,
)


class MaintenanceRequest(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "maintenance_requests"

    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    source_inspection_finding_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("inspection_findings.id"), nullable=True)

    maintenance_type: Mapped[MaintenanceType] = mapped_column(nullable=False)
    priority: Mapped[MaintenancePriority] = mapped_column(nullable=False, default=MaintenancePriority.MEDIUM)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_cost: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[MaintenanceRequestStatus] = mapped_column(nullable=False, default=MaintenanceRequestStatus.OPEN)
    requested_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    work_order: Mapped["WorkOrder | None"] = relationship(back_populates="maintenance_request", uselist=False)


class WorkOrder(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "work_orders"

    work_order_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    maintenance_request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("maintenance_requests.id", ondelete="CASCADE"), nullable=False)
    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)

    contractor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("contractors.id"), nullable=True)
    assigned_officer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    priority: Mapped[MaintenancePriority] = mapped_column(nullable=False, default=MaintenancePriority.MEDIUM)
    status: Mapped[WorkOrderStatus] = mapped_column(nullable=False, default=WorkOrderStatus.CREATED)

    sla_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    estimated_cost: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    actual_cost: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)

    completed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    completion_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    before_photo_document_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    after_photo_document_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    verified_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    verified_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    maintenance_request: Mapped["MaintenanceRequest"] = relationship(back_populates="work_order")
    records: Mapped[list["MaintenanceRecord"]] = relationship(back_populates="work_order", cascade="all, delete-orphan")


class MaintenanceRecord(UUIDPKMixin, TimestampMixin, Base):
    """Historical log entry appended as a work order progresses (status changes, notes, cost updates)."""

    __tablename__ = "maintenance_records"

    work_order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False)
    event: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    work_order: Mapped["WorkOrder"] = relationship(back_populates="records")
