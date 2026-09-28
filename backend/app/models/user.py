import uuid

from sqlalchemy import Boolean, ForeignKey, String, Table, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, UUIDPKMixin, TimestampMixin

RolePermission = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Permission(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)


class Role(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "roles"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=True)

    permissions: Mapped[list["Permission"]] = relationship(secondary=RolePermission)


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )
    # Optional scoping: restrict this role grant to a specific administrative unit
    jurisdiction_unit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("administrative_units.id"), nullable=True
    )

    role: Mapped["Role"] = relationship()


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True
    )
    # Home jurisdiction: the administrative unit this user is based at.
    # Combined with role grants, determines the subtree of assets/tasks visible to them.
    administrative_unit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("administrative_units.id"), nullable=True
    )

    department: Mapped["Department | None"] = relationship()
    administrative_unit: Mapped["AdministrativeUnit | None"] = relationship(foreign_keys=[administrative_unit_id])
    role_grants: Mapped[list["UserRole"]] = relationship(cascade="all, delete-orphan")
