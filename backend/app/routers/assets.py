from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.auth.deps import require_roles
from app.database import get_db
from app.models.asset import Asset, AssetType
from app.models.enums import AssetTypeCode, ConditionRating, LifecycleStatus, SystemRole
from app.models.lifecycle import LifecycleEvent
from app.models.user import User
from app.permissions.jurisdiction import apply_jurisdiction_filter
from app.schemas.asset import AssetCreate, AssetListItem, AssetRead, AssetUpdate, LifecycleTransitionRequest
from app.schemas.common import Page, paginate
from app.services import asset_service
from app.services.lifecycle_service import InvalidLifecycleTransition, transition_asset

router = APIRouter(prefix="/assets", tags=["assets"])

_DETAIL_LOADERS = [
    joinedload(Asset.geometry),
    joinedload(Asset.road_detail),
    joinedload(Asset.bridge_detail),
    joinedload(Asset.culvert_detail),
    joinedload(Asset.building_detail),
    joinedload(Asset.structure_detail),
]
_ASSET_READ_ROLES = [r.value for r in [
    SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN, SystemRole.FIELD_ENGINEER,
    SystemRole.MAINTENANCE_OFFICER,
]]


@router.get("", response_model=Page[AssetListItem])
def list_assets(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*_ASSET_READ_ROLES)),
    q: str | None = None,
    asset_type_code: AssetTypeCode | None = None,
    lifecycle_status: LifecycleStatus | None = None,
    current_condition: ConditionRating | None = None,
    administrative_unit_id: UUID | None = None,
    department_id: UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    query = db.query(Asset).filter(Asset.is_deleted.is_(False)).join(AssetType, Asset.asset_type_id == AssetType.id)
    query = apply_jurisdiction_filter(query, db, user, Asset.administrative_unit_id)

    if q:
        like = f"%{q}%"
        query = query.filter(or_(Asset.name.ilike(like), Asset.asset_code.ilike(like)))
    if asset_type_code:
        query = query.filter(AssetType.code == asset_type_code)
    if lifecycle_status:
        query = query.filter(Asset.lifecycle_status == lifecycle_status)
    if current_condition:
        query = query.filter(Asset.current_condition == current_condition)
    if administrative_unit_id:
        query = query.filter(Asset.administrative_unit_id == administrative_unit_id)
    if department_id:
        query = query.filter(Asset.department_id == department_id)

    total = query.count()
    rows = query.order_by(Asset.name).offset((page - 1) * page_size).limit(page_size).all()

    items = [
        AssetListItem(
            id=a.id,
            asset_code=a.asset_code,
            name=a.name,
            asset_type_code=db.get(AssetType, a.asset_type_id).code,
            lifecycle_status=a.lifecycle_status,
            current_condition=a.current_condition,
            administrative_unit_id=a.administrative_unit_id,
            department_id=a.department_id,
        )
        for a in rows
    ]
    return paginate(items, total, page, page_size)


@router.post("", response_model=AssetRead, status_code=201)
def create_asset(
    payload: AssetCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*[r.value for r in [
        SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN
    ]])),
):
    if db.query(Asset).filter(Asset.asset_code == payload.asset_code).first():
        raise HTTPException(status_code=409, detail="Asset code already exists")
    try:
        asset = asset_service.create_asset(db, payload, user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    asset = db.query(Asset).options(*_DETAIL_LOADERS).filter(Asset.id == asset.id).first()
    return asset_service.serialize_asset(db, asset)


@router.get("/{asset_id}", response_model=AssetRead)
def get_asset(asset_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(*_ASSET_READ_ROLES))):
    asset = db.query(Asset).options(*_DETAIL_LOADERS).filter(Asset.id == asset_id, Asset.is_deleted.is_(False)).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset_service.serialize_asset(db, asset)


@router.patch("/{asset_id}", response_model=AssetRead)
def update_asset(
    asset_id: UUID,
    payload: AssetUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*[r.value for r in [
        SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN
    ]])),
):
    asset = db.query(Asset).options(*_DETAIL_LOADERS).filter(Asset.id == asset_id, Asset.is_deleted.is_(False)).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    asset_service.update_asset(db, asset, payload, user)
    db.commit()
    db.refresh(asset)
    return asset_service.serialize_asset(db, asset)


@router.get("/{asset_id}/lifecycle-history")
def lifecycle_history(asset_id: UUID, db: Session = Depends(get_db), _=Depends(require_roles(*_ASSET_READ_ROLES))):
    events = (
        db.query(LifecycleEvent)
        .filter(LifecycleEvent.asset_id == asset_id)
        .order_by(LifecycleEvent.created_at.desc())
        .all()
    )
    return [
        {
            "id": e.id,
            "old_status": e.old_status,
            "new_status": e.new_status,
            "changed_by": e.changed_by,
            "reason": e.reason,
            "created_at": e.created_at,
        }
        for e in events
    ]


@router.post("/{asset_id}/lifecycle-transitions", response_model=AssetRead)
def create_lifecycle_transition(
    asset_id: UUID,
    payload: LifecycleTransitionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*[r.value for r in [
        SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN
    ]])),
):
    asset = db.query(Asset).options(*_DETAIL_LOADERS).filter(Asset.id == asset_id, Asset.is_deleted.is_(False)).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    try:
        transition_asset(db, asset, payload.new_status, user, payload.reason)
    except InvalidLifecycleTransition as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    db.refresh(asset)
    return asset_service.serialize_asset(db, asset)
