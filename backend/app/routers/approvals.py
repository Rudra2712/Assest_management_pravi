from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import require_roles
from app.database import get_db
from app.models.approval import Approval
from app.models.enums import ApprovalEntityType, ApprovalStatus, SystemRole
from app.schemas.approval import ApprovalRead

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("", response_model=list[ApprovalRead])
def list_approvals(
    db: Session = Depends(get_db),
    _=Depends(require_roles(*[r.value for r in [
        SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN,
    ]])),
    entity_type: ApprovalEntityType | None = None,
    status: ApprovalStatus | None = None,
    entity_id: UUID | None = None,
):
    query = db.query(Approval)
    if entity_type:
        query = query.filter(Approval.entity_type == entity_type)
    if status:
        query = query.filter(Approval.status == status)
    if entity_id:
        query = query.filter(Approval.entity_id == entity_id)
    return query.order_by(Approval.created_at.desc()).limit(500).all()
