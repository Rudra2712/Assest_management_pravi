import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, UUIDPKMixin, TimestampMixin


class Contractor(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "contractors"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    registration_number: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    contact_person: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    # Linked to a platform user account with role=CONTRACTOR so they can log in and see assigned work.
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)


class ContractorAssignment(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "contractor_assignments"

    contractor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contractors.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    work_order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("work_orders.id"), nullable=True)
    role_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
