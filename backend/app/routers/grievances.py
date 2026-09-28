import random
import string
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_roles
from app.database import get_db
from app.gis.geometry import geojson_to_geometry, geojson_to_geometry_kind
from app.models.asset import Asset
from app.models.enums import (
    FindingSeverity,
    GrievanceCategory,
    GrievanceStatus,
    MaintenancePriority,
    MaintenanceType,
    NotificationEvent,
    SystemRole,
)
from app.models.grievance import Grievance
from app.models.maintenance import MaintenanceRequest
from app.models.user import User
from app.permissions.jurisdiction import user_role_codes
from app.schemas.grievance import GrievanceAssign, GrievanceLinkAsset, GrievanceRead, GrievanceStatusUpdate
from app.services.notification_service import notify
from app.utils import storage
from app.utils.audit import record_audit

router = APIRouter(prefix="/grievances", tags=["grievances"])

_STAFF_ROLES = [r.value for r in [
    SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN,
    SystemRole.FIELD_ENGINEER, SystemRole.MAINTENANCE_OFFICER,
]]
_ALLOWED_STATUS_TRANSITIONS = {
    GrievanceStatus.OPEN: {GrievanceStatus.ACKNOWLEDGED, GrievanceStatus.IN_PROGRESS, GrievanceStatus.REJECTED},
    GrievanceStatus.ACKNOWLEDGED: {GrievanceStatus.IN_PROGRESS, GrievanceStatus.REJECTED},
    GrievanceStatus.IN_PROGRESS: {GrievanceStatus.RESOLVED, GrievanceStatus.REJECTED},
}


def _generate_code() -> str:
    return "GRV-" + "".join(random.choices(string.digits, k=8))


@router.get("/asset-lookup/{asset_id}")
def public_asset_lookup(asset_id: UUID, db: Session = Depends(get_db)):
    """Public (no auth) — the /report page needs just enough asset info to
    show 'Reporting against X' and re-center the map, without requiring the
    anonymous citizen filing the grievance to be logged in. GET /assets/{id}
    is intentionally staff-only since it returns financials/ownership."""
    asset = db.get(Asset, asset_id)
    if not asset or asset.is_deleted:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {
        "id": asset.id,
        "asset_code": asset.asset_code,
        "name": asset.name,
        "geometry": asset.geometry.geom if asset.geometry else None,
    }


def _to_read(g: Grievance) -> GrievanceRead:
    data = GrievanceRead.model_validate(g)
    data.has_photo = g.photo_storage_key is not None
    return data


@router.post("", response_model=GrievanceRead, status_code=201)
async def file_grievance(
    title: str = Form(...),
    description: str = Form(...),
    lat: float = Form(...),
    lon: float = Form(...),
    category: GrievanceCategory = Form(GrievanceCategory.OTHER),
    severity: FindingSeverity = Form(FindingSeverity.LOW),
    asset_id: UUID | None = Form(None),
    reporter_name: str | None = Form(None),
    reporter_contact: str | None = Form(None),
    photo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    """Public endpoint — anyone (citizen, field staff, contractor) can file a
    grievance with no login, e.g. 'tree root water-seepage damaging asphalt near
    KM 3' pinned to a map location. Staff triage and resolve it from the app."""

    location: dict[str, Any] = {"type": "Point", "coordinates": [lon, lat]}
    try:
        geojson_to_geometry_kind(location)
        location = geojson_to_geometry(location)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if asset_id and not db.get(Asset, asset_id):
        raise HTTPException(status_code=404, detail="Linked asset not found")

    grievance = Grievance(
        grievance_code=_generate_code(),
        title=title,
        description=description,
        category=category,
        severity=severity,
        location=location,
        asset_id=asset_id,
        reporter_name=reporter_name,
        reporter_contact=reporter_contact,
    )

    if photo is not None:
        content = await photo.read()
        try:
            storage.validate_upload(photo, len(content))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        storage_key = storage.build_storage_key("grievance", photo.filename or "photo.jpg")
        storage.save_file(storage_key, content)
        grievance.photo_storage_key = storage_key

    db.add(grievance)
    db.flush()
    record_audit(db, actor_id=None, action="GRIEVANCE_FILED", entity_type="grievance", entity_id=grievance.id, new_value={"category": category.value, "title": title})
    db.commit()
    db.refresh(grievance)
    return _to_read(grievance)


@router.get("", response_model=list[GrievanceRead])
def list_grievances(
    db: Session = Depends(get_db),
    _=Depends(require_roles(*_STAFF_ROLES)),
    status: GrievanceStatus | None = None,
    category: GrievanceCategory | None = None,
    asset_id: UUID | None = None,
):
    query = db.query(Grievance)
    if status:
        query = query.filter(Grievance.status == status)
    if category:
        query = query.filter(Grievance.category == category)
    if asset_id:
        query = query.filter(Grievance.asset_id == asset_id)
    rows = query.order_by(Grievance.created_at.desc()).limit(500).all()
    return [_to_read(g) for g in rows]


@router.get("/geojson")
def grievances_geojson(
    db: Session = Depends(get_db),
    _=Depends(require_roles(*_STAFF_ROLES)),
    status: GrievanceStatus | None = None,
):
    query = db.query(Grievance)
    if status:
        query = query.filter(Grievance.status == status)
    rows = query.limit(2000).all()
    features = [
        {
            "type": "Feature",
            "geometry": g.location,
            "properties": {
                "id": str(g.id),
                "grievance_code": g.grievance_code,
                "title": g.title,
                "category": g.category.value,
                "severity": g.severity.value,
                "status": g.status.value,
                "asset_id": str(g.asset_id) if g.asset_id else None,
            },
        }
        for g in rows
    ]
    return {"type": "FeatureCollection", "features": features}


@router.get("/{grievance_id}", response_model=GrievanceRead)
def get_grievance(grievance_id: UUID, db: Session = Depends(get_db), _=Depends(require_roles(*_STAFF_ROLES))):
    g = db.get(Grievance, grievance_id)
    if not g:
        raise HTTPException(status_code=404, detail="Grievance not found")
    return _to_read(g)


@router.get("/{grievance_id}/photo")
def get_grievance_photo(grievance_id: UUID, db: Session = Depends(get_db)):
    g = db.get(Grievance, grievance_id)
    if not g or not g.photo_storage_key:
        raise HTTPException(status_code=404, detail="No photo for this grievance")
    path = storage.resolve_path(g.photo_storage_key)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Photo missing from storage")
    return FileResponse(path)


@router.patch("/{grievance_id}/status", response_model=GrievanceRead)
def update_status(
    grievance_id: UUID,
    payload: GrievanceStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*_STAFF_ROLES)),
):
    g = db.get(Grievance, grievance_id)
    if not g:
        raise HTTPException(status_code=404, detail="Grievance not found")

    old_status = g.status
    if payload.status not in _ALLOWED_STATUS_TRANSITIONS.get(old_status, set()):
        raise HTTPException(status_code=409, detail=f"Cannot move a grievance from {old_status.value} to {payload.status.value}")
    g.status = payload.status
    if payload.status in (GrievanceStatus.RESOLVED, GrievanceStatus.REJECTED):
        if not payload.notes or not payload.notes.strip():
            raise HTTPException(status_code=400, detail="Resolution notes are required for a resolved or rejected grievance")
        g.resolution_notes = payload.notes
        g.resolved_by = user.id
        g.resolved_at = datetime.now(timezone.utc)

    record_audit(db, actor_id=user.id, action="GRIEVANCE_STATUS_UPDATE", entity_type="grievance", entity_id=g.id, old_value={"status": old_status.value}, new_value={"status": payload.status.value, "notes": payload.notes})
    db.commit()
    db.refresh(g)
    return _to_read(g)


@router.post("/{grievance_id}/assign", response_model=GrievanceRead)
def assign_grievance(
    grievance_id: UUID,
    payload: GrievanceAssign,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*_STAFF_ROLES)),
):
    g = db.get(Grievance, grievance_id)
    if not g:
        raise HTTPException(status_code=404, detail="Grievance not found")
    assignee = db.get(User, payload.assigned_to)
    if not assignee or not user_role_codes(assignee) & set(_STAFF_ROLES):
        raise HTTPException(status_code=400, detail="Assignee must be an active staff user")
    g.assigned_to = payload.assigned_to
    if g.status == GrievanceStatus.OPEN:
        g.status = GrievanceStatus.ACKNOWLEDGED
    notify(db, payload.assigned_to, NotificationEvent.GRIEVANCE_FILED, f"Grievance assigned: {g.title}", body=g.description, context={"grievance_id": str(g.id)})
    record_audit(db, actor_id=user.id, action="GRIEVANCE_ASSIGN", entity_type="grievance", entity_id=g.id, new_value={"assigned_to": str(payload.assigned_to)})
    db.commit()
    db.refresh(g)
    return _to_read(g)


@router.post("/{grievance_id}/link-asset", response_model=GrievanceRead)
def link_asset(
    grievance_id: UUID,
    payload: GrievanceLinkAsset,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*_STAFF_ROLES)),
):
    g = db.get(Grievance, grievance_id)
    if not g:
        raise HTTPException(status_code=404, detail="Grievance not found")
    if not db.get(Asset, payload.asset_id):
        raise HTTPException(status_code=404, detail="Asset not found")
    g.asset_id = payload.asset_id
    record_audit(db, actor_id=user.id, action="GRIEVANCE_LINK_ASSET", entity_type="grievance", entity_id=g.id, new_value={"asset_id": str(payload.asset_id)})
    db.commit()
    db.refresh(g)
    return _to_read(g)


@router.post("/{grievance_id}/convert-to-maintenance")
def convert_to_maintenance(
    grievance_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*_STAFF_ROLES)),
):
    g = db.get(Grievance, grievance_id)
    if not g:
        raise HTTPException(status_code=404, detail="Grievance not found")
    if not g.asset_id:
        raise HTTPException(status_code=400, detail="Link this grievance to an asset before converting it to a maintenance request")
    if g.linked_maintenance_request_id:
        raise HTTPException(status_code=409, detail="Already converted to a maintenance request")

    severity_to_priority = {
        FindingSeverity.LOW: MaintenancePriority.LOW,
        FindingSeverity.MEDIUM: MaintenancePriority.MEDIUM,
        FindingSeverity.HIGH: MaintenancePriority.HIGH,
        FindingSeverity.CRITICAL: MaintenancePriority.URGENT,
    }
    request = MaintenanceRequest(
        asset_id=g.asset_id,
        maintenance_type=MaintenanceType.CORRECTIVE,
        priority=severity_to_priority[g.severity],
        description=f"[From grievance {g.grievance_code}] {g.title}: {g.description}",
        requested_by=user.id,
    )
    db.add(request)
    db.flush()
    g.linked_maintenance_request_id = request.id
    g.status = GrievanceStatus.IN_PROGRESS

    record_audit(db, actor_id=user.id, action="GRIEVANCE_CONVERTED", entity_type="grievance", entity_id=g.id, new_value={"maintenance_request_id": str(request.id)})
    db.commit()
    return {"maintenance_request_id": request.id}
