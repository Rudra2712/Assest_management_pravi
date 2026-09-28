from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_roles
from app.database import get_db
from app.models.approval import Approval
from app.models.asset import Asset
from app.models.enums import ApprovalEntityType, ApprovalStatus, MaintenanceRequestStatus, SystemRole
from app.models.maintenance import MaintenanceRequest, WorkOrder
from app.models.user import User
from app.schemas.maintenance import MaintenanceRequestCreate, MaintenanceRequestDecision, MaintenanceRequestRead, WorkOrderCreate, WorkOrderRead
from app.utils.audit import record_audit

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.get("/requests", response_model=list[MaintenanceRequestRead])
def list_requests(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
    asset_id: UUID | None = None,
    status: MaintenanceRequestStatus | None = None,
):
    query = db.query(MaintenanceRequest)
    if asset_id:
        query = query.filter(MaintenanceRequest.asset_id == asset_id)
    if status:
        query = query.filter(MaintenanceRequest.status == status)
    return query.order_by(MaintenanceRequest.created_at.desc()).limit(500).all()


@router.post("/requests", response_model=MaintenanceRequestRead, status_code=201)
def create_request(payload: MaintenanceRequestCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    asset = db.get(Asset, payload.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    req = MaintenanceRequest(**payload.model_dump(), requested_by=user.id)
    db.add(req)
    db.flush()
    record_audit(db, actor_id=user.id, action="MAINTENANCE_REQUEST_CREATE", entity_type="maintenance_request", entity_id=req.id, new_value={"asset_id": str(asset.id)})
    db.commit()
    db.refresh(req)
    return req


@router.post("/requests/{request_id}/decision", response_model=MaintenanceRequestRead)
def decide_request(
    request_id: UUID,
    payload: MaintenanceRequestDecision,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*[r.value for r in [
        SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN, SystemRole.CIRCLE_DIVISION_OFFICER, SystemRole.SUB_DIVISION_OFFICER
    ]])),
):
    req = db.get(MaintenanceRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    if req.status != MaintenanceRequestStatus.OPEN:
        raise HTTPException(status_code=400, detail="Only open requests can be decided")

    req.status = MaintenanceRequestStatus.APPROVED if payload.approve else MaintenanceRequestStatus.REJECTED
    req.approved_by = user.id

    from datetime import datetime, timezone

    db.add(Approval(
        entity_type=ApprovalEntityType.MAINTENANCE_REQUEST,
        entity_id=req.id,
        submitted_by=req.requested_by,
        approver_id=user.id,
        status=ApprovalStatus.APPROVED if payload.approve else ApprovalStatus.REJECTED,
        comments=payload.comments,
        decided_at=datetime.now(timezone.utc),
    ))

    record_audit(db, actor_id=user.id, action="MAINTENANCE_REQUEST_DECISION", entity_type="maintenance_request", entity_id=req.id, new_value={"approved": payload.approve, "comments": payload.comments})
    db.commit()
    db.refresh(req)
    return req


@router.post("/requests/{request_id}/work-order", response_model=WorkOrderRead, status_code=201)
def create_work_order(
    request_id: UUID,
    payload: WorkOrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*[r.value for r in [
        SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN, SystemRole.CIRCLE_DIVISION_OFFICER,
        SystemRole.SUB_DIVISION_OFFICER, SystemRole.MAINTENANCE_OFFICER,
    ]])),
):
    req = db.get(MaintenanceRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    if req.status != MaintenanceRequestStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Maintenance request must be approved before a work order can be created")
    if req.work_order is not None:
        raise HTTPException(status_code=409, detail="A work order already exists for this request")

    import random
    import string

    code = "WO-" + "".join(random.choices(string.digits, k=8))

    work_order = WorkOrder(
        work_order_code=code,
        maintenance_request_id=req.id,
        asset_id=req.asset_id,
        estimated_cost=payload.estimated_cost or req.estimated_cost,
        **payload.model_dump(exclude={"estimated_cost"}),
    )
    db.add(work_order)
    req.status = MaintenanceRequestStatus.CONVERTED_TO_WORK_ORDER

    record_audit(db, actor_id=user.id, action="WORK_ORDER_CREATE", entity_type="work_order", entity_id=work_order.id, new_value={"maintenance_request_id": str(req.id)})
    db.commit()
    db.refresh(work_order)
    return work_order
