from datetime import datetime
from uuid import UUID

from app.models.enums import NotificationEvent
from app.schemas.common import ORMModel


class NotificationRead(ORMModel):
    id: UUID
    event: NotificationEvent
    title: str
    body: str | None = None
    context: dict | None = None
    is_read: bool
    created_at: datetime
