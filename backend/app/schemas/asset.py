from datetime import date
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import AssetTypeCode, ConditionRating, LifecycleStatus
from app.schemas.common import ORMModel


class RoadDetail(BaseModel):
    length_km: float | None = None
    width_m: float | None = None
    number_of_lanes: int | None = None
    surface_type: str | None = None
    start_point_desc: str | None = None
    end_point_desc: str | None = None
    traffic_info: str | None = None


class BridgeDetail(BaseModel):
    length_m: float | None = None
    width_m: float | None = None
    number_of_spans: int | None = None
    bridge_type: str | None = None
    material: str | None = None
    load_capacity_tonnes: float | None = None


class CulvertDetail(BaseModel):
    culvert_type: str | None = None
    length_m: float | None = None
    opening_width_m: float | None = None
    material: str | None = None


class BuildingDetail(BaseModel):
    plot_area_sqm: float | None = None
    built_up_area_sqm: float | None = None
    number_of_floors: int | None = None
    construction_year: int | None = None
    building_type: str | None = None
    occupancy_use: str | None = None


class StructureDetail(BaseModel):
    structure_subtype: str | None = None
    attributes: dict[str, Any] | None = None


class AssetBase(BaseModel):
    name: str
    description: str | None = None
    asset_type_code: AssetTypeCode
    category_id: UUID | None = None
    ownership: str | None = None
    department_id: UUID
    administrative_unit_id: UUID
    address: str | None = None
    acquisition_date: date | None = None
    commissioning_date: date | None = None
    original_cost: float | None = None
    current_value: float | None = None
    useful_life_years: int | None = None
    expected_end_of_life: date | None = None
    responsible_officer_id: UUID | None = None
    linked_project_id: UUID | None = None

    geometry: dict[str, Any] | None = Field(default=None, description="GeoJSON Point, LineString or Polygon")

    road: RoadDetail | None = None
    bridge: BridgeDetail | None = None
    culvert: CulvertDetail | None = None
    building: BuildingDetail | None = None
    structure: StructureDetail | None = None


class AssetCreate(AssetBase):
    asset_code: str


class AssetUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category_id: UUID | None = None
    ownership: str | None = None
    address: str | None = None
    acquisition_date: date | None = None
    commissioning_date: date | None = None
    original_cost: float | None = None
    current_value: float | None = None
    useful_life_years: int | None = None
    expected_end_of_life: date | None = None
    responsible_officer_id: UUID | None = None
    linked_project_id: UUID | None = None
    geometry: dict[str, Any] | None = None
    road: RoadDetail | None = None
    bridge: BridgeDetail | None = None
    culvert: CulvertDetail | None = None
    building: BuildingDetail | None = None
    structure: StructureDetail | None = None


class AssetListItem(ORMModel):
    id: UUID
    asset_code: str
    name: str
    asset_type_code: AssetTypeCode
    lifecycle_status: LifecycleStatus
    current_condition: ConditionRating | None = None
    administrative_unit_id: UUID
    department_id: UUID


class AssetRead(ORMModel):
    id: UUID
    asset_code: str
    name: str
    description: str | None = None
    asset_type_code: AssetTypeCode
    category_id: UUID | None = None
    ownership: str | None = None
    department_id: UUID
    administrative_unit_id: UUID
    address: str | None = None
    acquisition_date: date | None = None
    commissioning_date: date | None = None
    lifecycle_status: LifecycleStatus
    current_condition: ConditionRating | None = None
    original_cost: float | None = None
    current_value: float | None = None
    useful_life_years: int | None = None
    expected_end_of_life: date | None = None
    responsible_officer_id: UUID | None = None
    linked_project_id: UUID | None = None
    created_at: Any
    updated_at: Any

    geometry: dict[str, Any] | None = None
    road: RoadDetail | None = None
    bridge: BridgeDetail | None = None
    culvert: CulvertDetail | None = None
    building: BuildingDetail | None = None
    structure: StructureDetail | None = None


class LifecycleTransitionRequest(BaseModel):
    new_status: LifecycleStatus
    reason: str | None = None
