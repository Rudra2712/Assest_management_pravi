from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy.orm import Session, joinedload

from app.auth.deps import get_current_user, require_roles
from app.database import get_db
from app.gis.geometry import wkb_to_geojson
from app.models.approval import Approval
from app.models.asset import Asset
from app.models.condition import ConditionAssessment
from app.models.enums import (
    ApprovalEntityType,
    ApprovalStatus,
    InspectionStatus,
    MaintenanceRequestStatus,
    SystemRole,
)
from app.models.inspection import Inspection, InspectionFinding
from app.models.maintenance import MaintenanceRequest
from app.models.user import User
from app.schemas.inspection import InspectionAssign, InspectionRead, InspectionReview, InspectionSubmit
from app.services.condition_service import compute_condition
from app.utils.audit import record_audit

router = APIRouter(prefix="/inspections", tags=["inspections"])


def _to_read(inspection: Inspection) -> InspectionRead:
    data = InspectionRead.model_validate(inspection)
    data.gps = wkb_to_geojson(inspection.gps_point)
    return data


@router.get("", response_model=list[InspectionRead])
def list_inspections(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    mine: bool = False,
    asset_id: UUID | None = None,
    status: InspectionStatus | None = None,
):
    query = db.query(Inspection).options(joinedload(Inspection.findings))
    if mine:
        query = query.filter(Inspection.inspector_id == user.id)
    if asset_id:
        query = query.filter(Inspection.asset_id == asset_id)
    if status:
        query = query.filter(Inspection.status == status)
    rows = query.order_by(Inspection.created_at.desc()).limit(500).all()
    return [_to_read(r) for r in rows]


@router.get("/{inspection_id}", response_model=InspectionRead)
def get_inspection(inspection_id: UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    inspection = db.query(Inspection).options(joinedload(Inspection.findings)).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return _to_read(inspection)


@router.post("", response_model=InspectionRead, status_code=201)
def assign_inspection(
    payload: InspectionAssign,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*[r.value for r in [
        SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN, SystemRole.CIRCLE_DIVISION_OFFICER, SystemRole.SUB_DIVISION_OFFICER
    ]])),
):
    asset = db.get(Asset, payload.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    inspection = Inspection(
        asset_id=payload.asset_id,
        inspector_id=payload.inspector_id,
        template_id=payload.template_id,
        assigned_date=payload.assigned_date,
        status=InspectionStatus.ASSIGNED,
    )
    db.add(inspection)
    db.flush()
    record_audit(db, actor_id=user.id, action="INSPECTION_ASSIGN", entity_type="inspection", entity_id=inspection.id, new_value={"asset_id": str(asset.id), "inspector_id": str(payload.inspector_id)})
    db.commit()
    db.refresh(inspection)
    return _to_read(inspection)


@router.post("/{inspection_id}/submit", response_model=InspectionRead)
def submit_inspection(
    inspection_id: UUID,
    payload: InspectionSubmit,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    inspection = db.query(Inspection).options(joinedload(Inspection.findings)).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    if inspection.inspector_id != user.id:
        raise HTTPException(status_code=403, detail="Only the assigned inspector can submit this inspection")
    if inspection.status not in (InspectionStatus.ASSIGNED, InspectionStatus.IN_PROGRESS, InspectionStatus.RETURNED):
        raise HTTPException(status_code=400, detail=f"Cannot submit an inspection in status {inspection.status.value}")

    inspection.inspection_date = payload.inspection_date
    inspection.checklist_responses = payload.checklist_responses
    inspection.overall_condition = payload.overall_condition
    inspection.remarks = payload.remarks
    inspection.status = InspectionStatus.SUBMITTED
    if payload.gps_lat is not None and payload.gps_lon is not None:
        inspection.gps_point = from_shape(Point(payload.gps_lon, payload.gps_lat), srid=4326)

    for finding in inspection.findings:
        db.delete(finding)
    for f in payload.findings:
        db.add(InspectionFinding(inspection_id=inspection.id, **f.model_dump()))

    asset = db.get(Asset, inspection.asset_id)
    open_requests = db.query(MaintenanceRequest).filter(
        MaintenanceRequest.asset_id == asset.id,
        MaintenanceRequest.status.in_([MaintenanceRequestStatus.OPEN, MaintenanceRequestStatus.APPROVED]),
    ).count()
    result = compute_condition(asset, inspection, open_maintenance_request_count=open_requests)
    db.add(ConditionAssessment(asset_id=asset.id, inspection_id=inspection.id, assessed_by=user.id, **result))
    asset.current_condition = result["condition_rating"]

    record_audit(db, actor_id=user.id, action="INSPECTION_SUBMIT", entity_type="inspection", entity_id=inspection.id, new_value={"overall_condition": payload.overall_condition.value})
    db.commit()
    db.refresh(inspection)
    return _to_read(inspection)


@router.post("/{inspection_id}/review", response_model=InspectionRead)
def review_inspection(
    inspection_id: UUID,
    payload: InspectionReview,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*[r.value for r in [
        SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN, SystemRole.CIRCLE_DIVISION_OFFICER, SystemRole.SUB_DIVISION_OFFICER
    ]])),
):
    inspection = db.query(Inspection).options(joinedload(Inspection.findings)).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    if inspection.status != InspectionStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail="Only submitted inspections can be reviewed")

    from datetime import datetime, timezone

    inspection.reviewed_by = user.id
    inspection.reviewed_at = datetime.now(timezone.utc)
    inspection.review_comments = payload.comments
    inspection.status = InspectionStatus.APPROVED if payload.approve else InspectionStatus.RETURNED

    db.add(Approval(
        entity_type=ApprovalEntityType.INSPECTION,
        entity_id=inspection.id,
        submitted_by=inspection.inspector_id,
        approver_id=user.id,
        status=ApprovalStatus.APPROVED if payload.approve else ApprovalStatus.RETURNED,
        comments=payload.comments,
        decided_at=datetime.now(timezone.utc),
    ))

    record_audit(
        db, actor_id=user.id, action="INSPECTION_REVIEW", entity_type="inspection", entity_id=inspection.id,
        new_value={"approved": payload.approve, "comments": payload.comments},
    )
    db.commit()
    db.refresh(inspection)
    return _to_read(inspection)
