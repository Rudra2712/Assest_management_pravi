import uuid
from datetime import date, datetime

from sqlalchemy import ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import TenderBidStatus, TenderStatus


class Tender(UUIDPKMixin, TimestampMixin, Base):
    """A GeM-style public tender: publish a scope of work (often tied to an asset or
    project), take contractor bids, and award one. `tender_number` is the
    GeM-equivalent reference shown to the public/vendors."""

    __tablename__ = "tenders"

    tender_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[TenderStatus] = mapped_column(nullable=False, default=TenderStatus.DRAFT)

    asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False)
    administrative_unit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("administrative_units.id"), nullable=False)

    estimated_value: Mapped[float | None] = mapped_column(Numeric(16, 2), nullable=True)
    emd_amount: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    published_date: Mapped[date | None] = mapped_column(nullable=True)
    submission_deadline: Mapped[date | None] = mapped_column(nullable=True)

    awarded_bid_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tender_bids.id", use_alter=True, name="fk_tenders_awarded_bid_id"), nullable=True
    )
    awarded_at: Mapped[datetime | None] = mapped_column(nullable=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    asset: Mapped["Asset | None"] = relationship(foreign_keys=[asset_id])  # noqa: F821
    bids: Mapped[list["TenderBid"]] = relationship(back_populates="tender", foreign_keys="TenderBid.tender_id", cascade="all, delete-orphan")
    awarded_bid: Mapped["TenderBid | None"] = relationship(foreign_keys=[awarded_bid_id], post_update=True)


class TenderBid(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "tender_bids"
    __table_args__ = (UniqueConstraint("tender_id", "contractor_id", name="uq_tender_bid_contractor"),)

    tender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False)
    contractor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contractors.id"), nullable=False)
    bid_amount: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TenderBidStatus] = mapped_column(nullable=False, default=TenderBidStatus.SUBMITTED)

    tender: Mapped["Tender"] = relationship(back_populates="bids", foreign_keys=[tender_id])
    contractor: Mapped["Contractor"] = relationship()  # noqa: F821
