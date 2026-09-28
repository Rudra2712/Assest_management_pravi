from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def record_audit(
    db: Session,
    *,
    actor_id: Optional[UUID],
    action: str,
    entity_type: str,
    entity_id: UUID,
    old_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
    request_ip: str | None = None,
) -> AuditLog:
    """Writes an immutable audit trail row. Callers commit as part of their
    own transaction so the audit entry and the business change land atomically."""

    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        request_ip=request_ip,
    )
    db.add(entry)
    return entry
