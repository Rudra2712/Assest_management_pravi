"""In-app notifications, generated synchronously during the API call that
triggers them (no Celery/Redis for the hackathon MVP). Email/SMS are
future-scope dispatch flags only — see Notification.email_dispatch_requested."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.enums import NotificationEvent
from app.models.notification import Notification


def notify(db: Session, recipient_id: UUID, event: NotificationEvent, title: str, body: str | None = None, context: dict | None = None) -> Notification:
    n = Notification(recipient_id=recipient_id, event=event, title=title, body=body, context=context)
    db.add(n)
    return n
