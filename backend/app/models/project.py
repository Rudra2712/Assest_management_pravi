import uuid
from datetime import date

from sqlalchemy import ForeignKey, String, Text, Numeric, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, UUIDPKMixin, TimestampMixin
from app.models.enums import ProjectStatus


class Project(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    project_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(nullable=False, default=ProjectStatus.PROPOSED)

    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False)
    administrative_unit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("administrative_units.id"), nullable=False)

    sanctioned_budget: Mapped[float | None] = mapped_column(Numeric(16, 2), nullable=True)
    actual_expenditure: Mapped[float | None] = mapped_column(Numeric(16, 2), nullable=True)

    sanction_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expected_completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    contractor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("contractors.id"), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)


class ProjectAsset(Base):
    __tablename__ = "project_assets"

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True)
