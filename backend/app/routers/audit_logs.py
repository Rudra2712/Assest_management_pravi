from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.deps import require_roles
from app.database import get_db
from app.models.audit import AuditLog
from app.models.enums import SystemRole
from app.schemas.common import ORMModel

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


class AuditLogRead(ORMModel):
    id: UUID
    actor_id: UUID | None = None
    action: str
    entity_type: str
    entity_id: UUID
    old_value: dict | None = None
    new_value: dict | None = None
    created_at: datetime


@router.get("", response_model=list[AuditLogRead])
def list_audit_logs(
    db: Session = Depends(get_db),
    _=Depends(require_roles(SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN, SystemRole.AUDITOR)),
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    actor_id: UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
):
    query = db.query(AuditLog)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id)
    if actor_id:
        query = query.filter(AuditLog.actor_id == actor_id)
    return (
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
