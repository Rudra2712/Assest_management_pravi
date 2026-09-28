from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationRead

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
def list_my_notifications(unread_only: bool = False, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Notification).filter(Notification.recipient_id == user.id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))
    return query.order_by(Notification.created_at.desc()).limit(200).all()


@router.post("/{notification_id}/read", response_model=NotificationRead)
def mark_read(notification_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from datetime import datetime, timezone

    n = db.get(Notification, notification_id)
    if not n or n.recipient_id != user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.is_read = True
    n.read_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(n)
    return n
