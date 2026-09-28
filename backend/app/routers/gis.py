from uuid import UUID

from fastapi import APIRouter, Depends, Query
from geoalchemy2 import functions as geofunc
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.gis.geometry import wkb_to_geojson
from app.models.asset import Asset, AssetGeometry, AssetType
from app.models.enums import AssetTypeCode, ConditionRating, LifecycleStatus
from app.models.user import User
from app.permissions.jurisdiction import apply_jurisdiction_filter

router = APIRouter(prefix="/gis", tags=["gis"])


def _base_query(db: Session, user: User):
    query = (
        db.query(Asset, AssetGeometry, AssetType)
        .join(AssetGeometry, AssetGeometry.asset_id == Asset.id)
        .join(AssetType, AssetType.id == Asset.asset_type_id)
        .filter(Asset.is_deleted.is_(False))
    )
    return apply_jurisdiction_filter(query, db, user, Asset.administrative_unit_id)


def _to_feature(asset: Asset, geom: AssetGeometry, asset_type: AssetType) -> dict:
    return {
        "type": "Feature",
        "geometry": wkb_to_geojson(geom.geom),
        "properties": {
            "id": str(asset.id),
            "asset_code": asset.asset_code,
            "name": asset.name,
            "asset_type_code": asset_type.code.value,
            "lifecycle_status": asset.lifecycle_status.value,
            "current_condition": asset.current_condition.value if asset.current_condition else None,
            "administrative_unit_id": str(asset.administrative_unit_id),
        },
    }


@router.get("/assets.geojson")
def assets_geojson(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    asset_type_code: AssetTypeCode | None = None,
    lifecycle_status: LifecycleStatus | None = None,
    current_condition: ConditionRating | None = None,
    administrative_unit_id: UUID | None = None,
):
    query = _base_query(db, user)
    if asset_type_code:
        query = query.filter(AssetType.code == asset_type_code)
    if lifecycle_status:
        query = query.filter(Asset.lifecycle_status == lifecycle_status)
    if current_condition:
        query = query.filter(Asset.current_condition == current_condition)
    if administrative_unit_id:
        query = query.filter(Asset.administrative_unit_id == administrative_unit_id)

    rows = query.limit(5000).all()
    return {"type": "FeatureCollection", "features": [_to_feature(a, g, t) for a, g, t in rows]}


@router.get("/nearby.geojson")
def nearby_assets(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius_m: float = Query(1000, gt=0, le=50000),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    point = geofunc.ST_SetSRID(geofunc.ST_MakePoint(lon, lat), 4326)
    query = _base_query(db, user).filter(
        geofunc.ST_DWithin(geofunc.ST_Transform(AssetGeometry.geom, 3857), geofunc.ST_Transform(point, 3857), radius_m)
    )
    rows = query.limit(500).all()
    return {"type": "FeatureCollection", "features": [_to_feature(a, g, t) for a, g, t in rows]}
