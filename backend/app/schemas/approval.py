from datetime import datetime
from uuid import UUID

from app.models.enums import ApprovalEntityType, ApprovalStatus
from app.schemas.common import ORMModel


class ApprovalRead(ORMModel):
    id: UUID
    entity_type: ApprovalEntityType
    entity_id: UUID
    submitted_by: UUID
    approver_id: UUID | None = None
    status: ApprovalStatus
    comments: str | None = None
    decided_at: datetime | None = None
    created_at: datetime
