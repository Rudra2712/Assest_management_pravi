import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, UUIDPKMixin, TimestampMixin
from app.models.enums import NotificationEvent


class Notification(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "notifications"

    recipient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    event: Mapped[NotificationEvent] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Delivery abstraction: MVP only delivers in-app; these flags mark whether an
    # email/SMS adapter (not implemented) would have fired, for future wiring.
    email_dispatch_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    sms_dispatch_requested: Mapped[bool] = mapped_column(Boolean, default=False)
