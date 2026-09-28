import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, UUIDPKMixin, TimestampMixin
from app.models.enums import AdminUnitLevel


class Department(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "departments"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)


class AdministrativeUnit(UUIDPKMixin, TimestampMixin, Base):
    """
    Self-referencing hierarchy: State -> Region/Circle -> Division -> Sub-Division -> Section/Field Office.
    `path` stores materialized ancestor ids (e.g. "state_id.circle_id.division_id") to make
    subtree jurisdiction filtering a single LIKE/prefix query instead of a recursive CTE per request.
    """

    __tablename__ = "administrative_units"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[AdminUnitLevel] = mapped_column(nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("administrative_units.id"), nullable=True
    )
    path: Mapped[str] = mapped_column(String(1000), nullable=False, default="", index=True)

    parent: Mapped["AdministrativeUnit | None"] = relationship(remote_side="AdministrativeUnit.id")
