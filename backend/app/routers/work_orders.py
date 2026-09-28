from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_roles
from app.database import get_db
from app.models.asset import Asset
from app.models.contractor import Contractor
from app.models.enums import LifecycleStatus, SystemRole, WorkOrderStatus
from app.models.maintenance import MaintenanceRecord, WorkOrder
from app.models.user import User
from app.schemas.maintenance import WorkOrderAssign, WorkOrderComplete, WorkOrderRead, WorkOrderVerify
from app.services.lifecycle_service import ALLOWED_TRANSITIONS, transition_asset
from app.utils.audit import record_audit
from app.permissions.jurisdiction import user_role_codes

router = APIRouter(prefix="/work-orders", tags=["work-orders"])

_MAINTENANCE_ROLES = [r.value for r in [
    SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN, SystemRole.MAINTENANCE_OFFICER,
]]


def _require_work_order_access(db: Session, work_order: WorkOrder, user: User) -> None:
    roles = user_role_codes(user)
    if roles & set(_MAINTENANCE_ROLES):
        return
    contractor = db.query(Contractor).filter(Contractor.user_id == user.id).first()
    if SystemRole.CONTRACTOR.value in roles and contractor and work_order.contractor_id == contractor.id:
        return
    raise HTTPException(status_code=404, detail="Work order not found")


@router.get("", response_model=list[WorkOrderRead])
def list_work_orders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    asset_id: UUID | None = None,
    status: WorkOrderStatus | None = None,
    contractor_id: UUID | None = None,
):
    query = db.query(WorkOrder)
    roles = user_role_codes(user)
    if SystemRole.CONTRACTOR.value in roles:
        contractor = db.query(Contractor).filter(Contractor.user_id == user.id).first()
        if not contractor:
            return []
        query = query.filter(WorkOrder.contractor_id == contractor.id)
        if contractor_id and contractor_id != contractor.id:
            return []
    elif not roles & set(_MAINTENANCE_ROLES):
        raise HTTPException(status_code=403, detail="Insufficient role to view work orders")
    if asset_id:
        query = query.filter(WorkOrder.asset_id == asset_id)
    if status:
        query = query.filter(WorkOrder.status == status)
    if contractor_id:
        query = query.filter(WorkOrder.contractor_id == contractor_id)
    return query.order_by(WorkOrder.created_at.desc()).limit(500).all()


@router.get("/{work_order_id}", response_model=WorkOrderRead)
def get_work_order(work_order_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    wo = db.get(WorkOrder, work_order_id)
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    _require_work_order_access(db, wo, user)
    return wo


@router.post("/{work_order_id}/assign", response_model=WorkOrderRead)
def assign_work_order(
    work_order_id: UUID,
    payload: WorkOrderAssign,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*_MAINTENANCE_ROLES)),
):
    wo = db.get(WorkOrder, work_order_id)
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    if wo.status not in (WorkOrderStatus.CREATED, WorkOrderStatus.ASSIGNED):
        raise HTTPException(status_code=400, detail=f"Cannot assign a work order in status {wo.status.value}")

    if payload.contractor_id is not None:
        wo.contractor_id = payload.contractor_id
    if payload.assigned_officer_id is not None:
        wo.assigned_officer_id = payload.assigned_officer_id
    wo.status = WorkOrderStatus.ASSIGNED

    db.add(MaintenanceRecord(work_order_id=wo.id, event="ASSIGNED", recorded_by=user.id))
    record_audit(db, actor_id=user.id, action="WORK_ORDER_ASSIGN", entity_type="work_order", entity_id=wo.id, new_value=payload.model_dump(exclude_unset=True, mode="json"))
    db.commit()
    db.refresh(wo)
    return wo


@router.post("/{work_order_id}/start", response_model=WorkOrderRead)
def start_work_order(work_order_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    wo = db.get(WorkOrder, work_order_id)
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    _require_work_order_access(db, wo, user)
    if wo.status != WorkOrderStatus.ASSIGNED:
        raise HTTPException(status_code=400, detail="Work order must be assigned before it can start")

    wo.status = WorkOrderStatus.IN_PROGRESS
    asset = db.get(Asset, wo.asset_id)
    if LifecycleStatus.UNDER_MAINTENANCE in ALLOWED_TRANSITIONS.get(asset.lifecycle_status, set()):
        transition_asset(db, asset, LifecycleStatus.UNDER_MAINTENANCE, user, "Work order started")

    db.add(MaintenanceRecord(work_order_id=wo.id, event="STARTED", recorded_by=user.id))
    record_audit(db, actor_id=user.id, action="WORK_ORDER_START", entity_type="work_order", entity_id=wo.id)
    db.commit()
    db.refresh(wo)
    return wo


@router.post("/{work_order_id}/complete", response_model=WorkOrderRead)
def complete_work_order(
    work_order_id: UUID,
    payload: WorkOrderComplete,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    wo = db.get(WorkOrder, work_order_id)
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    _require_work_order_access(db, wo, user)
    if wo.status != WorkOrderStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Work order must be in progress to complete")

    wo.status = WorkOrderStatus.COMPLETED
    wo.completed_at = date.today()
    wo.actual_cost = payload.actual_cost
    wo.completion_remarks = payload.completion_remarks
    wo.before_photo_document_ids = payload.before_photo_document_ids
    wo.after_photo_document_ids = payload.after_photo_document_ids

    db.add(MaintenanceRecord(work_order_id=wo.id, event="COMPLETED", notes=payload.completion_remarks, recorded_by=user.id))
    record_audit(db, actor_id=user.id, action="WORK_ORDER_COMPLETE", entity_type="work_order", entity_id=wo.id, new_value={"actual_cost": payload.actual_cost})
    db.commit()
    db.refresh(wo)
    return wo


@router.post("/{work_order_id}/verify", response_model=WorkOrderRead)
def verify_work_order(
    work_order_id: UUID,
    payload: WorkOrderVerify,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*[r.value for r in [
        SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN
    ]])),
):
    wo = db.get(WorkOrder, work_order_id)
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    if wo.status != WorkOrderStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Work order must be completed before verification")

    wo.status = WorkOrderStatus.VERIFIED if payload.verified else WorkOrderStatus.IN_PROGRESS
    wo.verified_by = user.id
    wo.verified_at = date.today()

    if payload.verified:
        wo.status = WorkOrderStatus.CLOSED
        asset = db.get(Asset, wo.asset_id)
        if asset.lifecycle_status == LifecycleStatus.UNDER_MAINTENANCE:
            transition_asset(db, asset, LifecycleStatus.OPERATIONAL, user, "Maintenance work order verified and closed")

    db.add(MaintenanceRecord(work_order_id=wo.id, event="VERIFIED" if payload.verified else "VERIFICATION_REJECTED", notes=payload.comments, recorded_by=user.id))
    record_audit(db, actor_id=user.id, action="WORK_ORDER_VERIFY", entity_type="work_order", entity_id=wo.id, new_value={"verified": payload.verified})
    db.commit()
    db.refresh(wo)
    return wo


@router.get("/{work_order_id}/history")
def work_order_history(work_order_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    work_order = db.get(WorkOrder, work_order_id)
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    _require_work_order_access(db, work_order, user)
    records = db.query(MaintenanceRecord).filter(MaintenanceRecord.work_order_id == work_order_id).order_by(MaintenanceRecord.created_at).all()
    return [{"id": r.id, "event": r.event, "notes": r.notes, "recorded_by": r.recorded_by, "created_at": r.created_at} for r in records]
