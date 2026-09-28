from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_roles
from app.database import get_db
from app.models.asset import Asset
from app.models.condition import ConditionAssessment
from app.models.enums import MaintenanceRequestStatus, SystemRole
from app.models.maintenance import MaintenanceRequest
from app.models.user import User
from app.schemas.condition import ConditionAssessmentRead
from app.services.condition_service import compute_condition

router = APIRouter(prefix="/condition", tags=["condition"])


@router.get("/assets/{asset_id}/history", response_model=list[ConditionAssessmentRead])
def condition_history(asset_id: UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    rows = (
        db.query(ConditionAssessment)
        .filter(ConditionAssessment.asset_id == asset_id)
        .order_by(ConditionAssessment.created_at.desc())
        .all()
    )
    return rows


@router.post("/assets/{asset_id}/recompute", response_model=ConditionAssessmentRead)
def recompute_condition(
    asset_id: UUID,
    criticality: float = 0.5,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*[r.value for r in [
        SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN, SystemRole.CIRCLE_DIVISION_OFFICER, SystemRole.SUB_DIVISION_OFFICER
    ]])),
):
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    open_requests = db.query(MaintenanceRequest).filter(
        MaintenanceRequest.asset_id == asset.id,
        MaintenanceRequest.status.in_([MaintenanceRequestStatus.OPEN, MaintenanceRequestStatus.APPROVED]),
    ).count()
    result = compute_condition(asset, inspection=None, open_maintenance_request_count=open_requests, criticality=criticality)
    assessment = ConditionAssessment(asset_id=asset.id, assessed_by=user.id, **result)
    db.add(assessment)
    asset.current_condition = result["condition_rating"]
    db.commit()
    db.refresh(assessment)
    return assessment
