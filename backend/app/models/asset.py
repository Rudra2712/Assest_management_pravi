import uuid
from datetime import date

from sqlalchemy import ForeignKey, String, Numeric, Date, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, UUIDPKMixin, TimestampMixin
from app.models.enums import AssetTypeCode, LifecycleStatus, ConditionRating, GeometryKind


class AssetCategory(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "asset_categories"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)


class AssetType(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "asset_types"

    code: Mapped[AssetTypeCode] = mapped_column(unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_geometry_kind: Mapped[GeometryKind] = mapped_column(nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("asset_categories.id"), nullable=True
    )


class Asset(UUIDPKMixin, TimestampMixin, Base):
    """Common asset entity. Type-specific attributes live in the linked detail table
    (Road/Bridge/Culvert/Building/Structure) rather than as columns here."""

    __tablename__ = "assets"

    asset_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    asset_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("asset_types.id"), nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("asset_categories.id"), nullable=True)

    ownership: Mapped[str] = mapped_column(String(255), nullable=True)
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False)
    administrative_unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("administrative_units.id"), nullable=False, index=True
    )

    address: Mapped[str] = mapped_column(String(500), nullable=True)

    acquisition_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    commissioning_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    lifecycle_status: Mapped[LifecycleStatus] = mapped_column(nullable=False, default=LifecycleStatus.PLANNED)
    current_condition: Mapped[ConditionRating | None] = mapped_column(nullable=True)

    original_cost: Mapped[float | None] = mapped_column(Numeric(16, 2), nullable=True)
    current_value: Mapped[float | None] = mapped_column(Numeric(16, 2), nullable=True)
    useful_life_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expected_end_of_life: Mapped[date | None] = mapped_column(Date, nullable=True)

    responsible_officer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    linked_project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    is_deleted: Mapped[bool] = mapped_column(default=False)

    asset_type: Mapped["AssetType"] = relationship()
    administrative_unit: Mapped["AdministrativeUnit"] = relationship()  # noqa: F821
    geometry: Mapped["AssetGeometry | None"] = relationship(back_populates="asset", uselist=False, cascade="all, delete-orphan")
    road_detail: Mapped["Road | None"] = relationship(back_populates="asset", uselist=False, cascade="all, delete-orphan")
    bridge_detail: Mapped["Bridge | None"] = relationship(back_populates="asset", uselist=False, cascade="all, delete-orphan")
    culvert_detail: Mapped["Culvert | None"] = relationship(back_populates="asset", uselist=False, cascade="all, delete-orphan")
    building_detail: Mapped["Building | None"] = relationship(back_populates="asset", uselist=False, cascade="all, delete-orphan")
    structure_detail: Mapped["Structure | None"] = relationship(back_populates="asset", uselist=False, cascade="all, delete-orphan")


class AssetGeometry(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "asset_geometries"

    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), unique=True, nullable=False)
    geometry_kind: Mapped[GeometryKind] = mapped_column(nullable=False)
    geom: Mapped[dict] = mapped_column(JSONB, nullable=False)

    asset: Mapped["Asset"] = relationship(back_populates="geometry")


class AssetRelationship(UUIDPKMixin, TimestampMixin, Base):
    """Generic linkage between assets, e.g. a culvert located along a road, or a building on a plot."""

    __tablename__ = "asset_relationships"

    parent_asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    child_asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False, default="RELATED")


class Road(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "roads"

    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), unique=True, nullable=False)
    length_km: Mapped[float | None] = mapped_column(Numeric(10, 3), nullable=True)
    width_m: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    number_of_lanes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    surface_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    start_point_desc: Mapped[str | None] = mapped_column(String(255), nullable=True)
    end_point_desc: Mapped[str | None] = mapped_column(String(255), nullable=True)
    traffic_info: Mapped[str | None] = mapped_column(String(500), nullable=True)

    asset: Mapped["Asset"] = relationship(back_populates="road_detail")


class Bridge(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "bridges"

    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), unique=True, nullable=False)
    length_m: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    width_m: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    number_of_spans: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bridge_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    material: Mapped[str | None] = mapped_column(String(100), nullable=True)
    load_capacity_tonnes: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)

    asset: Mapped["Asset"] = relationship(back_populates="bridge_detail")


class Culvert(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "culverts"

    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), unique=True, nullable=False)
    culvert_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    length_m: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    opening_width_m: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    material: Mapped[str | None] = mapped_column(String(100), nullable=True)

    asset: Mapped["Asset"] = relationship(back_populates="culvert_detail")


class Building(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "buildings"

    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), unique=True, nullable=False)
    plot_area_sqm: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    built_up_area_sqm: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    number_of_floors: Mapped[int | None] = mapped_column(Integer, nullable=True)
    construction_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    building_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    occupancy_use: Mapped[str | None] = mapped_column(String(255), nullable=True)

    asset: Mapped["Asset"] = relationship(back_populates="building_detail")


class Structure(UUIDPKMixin, TimestampMixin, Base):
    """PUBLIC_STRUCTURE / OTHER_FIXED_ASSET: configurable attribute bag for asset types
    that don't warrant a dedicated table yet."""

    __tablename__ = "structures"

    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), unique=True, nullable=False)
    structure_subtype: Mapped[str | None] = mapped_column(String(100), nullable=True)
    attributes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    asset: Mapped["Asset"] = relationship(back_populates="structure_detail")
