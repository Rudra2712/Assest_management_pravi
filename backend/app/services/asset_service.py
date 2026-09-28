from uuid import UUID

from sqlalchemy.orm import Session

from app.gis.geometry import geojson_to_geometry_kind, geojson_to_wkb, wkb_to_geojson
from app.models.asset import (
    Asset,
    AssetGeometry,
    AssetType,
    Bridge,
    Building,
    Culvert,
    Road,
    Structure,
)
from app.models.enums import AssetTypeCode
from app.models.user import User
from app.utils.audit import record_audit

_DETAIL_MODEL_BY_TYPE: dict[AssetTypeCode, tuple[type, str]] = {
    AssetTypeCode.ROAD: (Road, "road"),
    AssetTypeCode.BRIDGE: (Bridge, "bridge"),
    AssetTypeCode.CULVERT: (Culvert, "culvert"),
    AssetTypeCode.BUILDING: (Building, "building"),
    AssetTypeCode.PUBLIC_STRUCTURE: (Structure, "structure"),
    AssetTypeCode.OTHER_FIXED_ASSET: (Structure, "structure"),
}


def get_asset_type(db: Session, code: AssetTypeCode) -> AssetType:
    asset_type = db.query(AssetType).filter(AssetType.code == code).first()
    if not asset_type:
        raise ValueError(f"Asset type '{code}' is not registered. Seed asset_types first.")
    return asset_type


def _apply_detail(db: Session, asset: Asset, asset_type_code: AssetTypeCode, payload) -> None:
    model_cls, field_name = _DETAIL_MODEL_BY_TYPE[asset_type_code]
    detail_payload = getattr(payload, field_name, None)
    if detail_payload is None:
        return
    detail = model_cls(asset_id=asset.id, **detail_payload.model_dump(exclude_unset=True))
    db.add(detail)


def _apply_geometry(db: Session, asset: Asset, geojson: dict | None) -> None:
    if geojson is None:
        return
    kind = geojson_to_geometry_kind(geojson)
    wkb = geojson_to_wkb(geojson)
    existing = db.query(AssetGeometry).filter(AssetGeometry.asset_id == asset.id).first()
    if existing:
        existing.geometry_kind = kind
        existing.geom = wkb
    else:
        db.add(AssetGeometry(asset_id=asset.id, geometry_kind=kind, geom=wkb))


def create_asset(db: Session, payload, user: User) -> Asset:
    asset_type = get_asset_type(db, payload.asset_type_code)

    asset = Asset(
        asset_code=payload.asset_code,
        name=payload.name,
        description=payload.description,
        asset_type_id=asset_type.id,
        category_id=payload.category_id,
        ownership=payload.ownership,
        department_id=payload.department_id,
        administrative_unit_id=payload.administrative_unit_id,
        address=payload.address,
        acquisition_date=payload.acquisition_date,
        commissioning_date=payload.commissioning_date,
        original_cost=payload.original_cost,
        current_value=payload.current_value,
        useful_life_years=payload.useful_life_years,
        expected_end_of_life=payload.expected_end_of_life,
        responsible_officer_id=payload.responsible_officer_id,
        linked_project_id=payload.linked_project_id,
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(asset)
    db.flush()

    _apply_detail(db, asset, payload.asset_type_code, payload)
    _apply_geometry(db, asset, payload.geometry)

    record_audit(db, actor_id=user.id, action="ASSET_CREATE", entity_type="asset", entity_id=asset.id, new_value={"asset_code": asset.asset_code, "name": asset.name})
    return asset


def update_asset(db: Session, asset: Asset, payload, user: User) -> Asset:
    old_value = {"name": asset.name, "current_value": float(asset.current_value) if asset.current_value else None}

    update_fields = payload.model_dump(exclude_unset=True, exclude={"road", "bridge", "culvert", "building", "structure", "geometry"})
    for field, value in update_fields.items():
        setattr(asset, field, value)
    asset.updated_by = user.id

    asset_type = db.get(AssetType, asset.asset_type_id)
    model_cls, field_name = _DETAIL_MODEL_BY_TYPE[asset_type.code]
    detail_payload = getattr(payload, field_name, None)
    if detail_payload is not None:
        existing_detail = getattr(asset, f"{field_name}_detail", None)
        if existing_detail:
            for k, v in detail_payload.model_dump(exclude_unset=True).items():
                setattr(existing_detail, k, v)
        else:
            db.add(model_cls(asset_id=asset.id, **detail_payload.model_dump(exclude_unset=True)))

    if payload.geometry is not None:
        _apply_geometry(db, asset, payload.geometry)

    record_audit(db, actor_id=user.id, action="ASSET_UPDATE", entity_type="asset", entity_id=asset.id, old_value=old_value, new_value=update_fields)
    return asset


def serialize_asset(db: Session, asset: Asset) -> dict:
    asset_type = db.get(AssetType, asset.asset_type_id)
    detail = None
    for attr in ("road_detail", "bridge_detail", "culvert_detail", "building_detail", "structure_detail"):
        value = getattr(asset, attr, None)
        if value is not None:
            detail = value
            detail_field = attr.replace("_detail", "")
            break
    else:
        detail_field = None

    data = {
        "id": asset.id,
        "asset_code": asset.asset_code,
        "name": asset.name,
        "description": asset.description,
        "asset_type_code": asset_type.code,
        "category_id": asset.category_id,
        "ownership": asset.ownership,
        "department_id": asset.department_id,
        "administrative_unit_id": asset.administrative_unit_id,
        "address": asset.address,
        "acquisition_date": asset.acquisition_date,
        "commissioning_date": asset.commissioning_date,
        "lifecycle_status": asset.lifecycle_status,
        "current_condition": asset.current_condition,
        "original_cost": asset.original_cost,
        "current_value": asset.current_value,
        "useful_life_years": asset.useful_life_years,
        "expected_end_of_life": asset.expected_end_of_life,
        "responsible_officer_id": asset.responsible_officer_id,
        "linked_project_id": asset.linked_project_id,
        "created_at": asset.created_at,
        "updated_at": asset.updated_at,
        "geometry": wkb_to_geojson(asset.geometry.geom) if asset.geometry else None,
        "road": None,
        "bridge": None,
        "culvert": None,
        "building": None,
        "structure": None,
    }
    if detail_field:
        data[detail_field] = detail
    return data
