"""grievances and tenders

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.enums import (
    FindingSeverity,
    GrievanceCategory,
    GrievanceStatus,
    TenderBidStatus,
    TenderStatus,
)

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _enum(pyenum, name):
    return sa.Enum(pyenum, name=name)


def upgrade() -> None:
    ts_cols = lambda: [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]

    op.create_table(
        "grievances",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("grievance_code", sa.String(50), unique=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("category", _enum(GrievanceCategory, "grievance_category"), nullable=False, server_default=GrievanceCategory.OTHER.value),
        sa.Column("severity", _enum(FindingSeverity, "finding_severity"), nullable=False, server_default=FindingSeverity.LOW.value),
        sa.Column("status", _enum(GrievanceStatus, "grievance_status"), nullable=False, server_default=GrievanceStatus.OPEN.value),
        sa.Column("location", JSONB, nullable=False),
        sa.Column("asset_id", UUID(as_uuid=True), sa.ForeignKey("assets.id"), nullable=True),
        sa.Column("photo_storage_key", sa.String(1000), nullable=True),
        sa.Column("reporter_name", sa.String(255), nullable=True),
        sa.Column("reporter_contact", sa.String(255), nullable=True),
        sa.Column("reported_by_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("assigned_to", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("linked_maintenance_request_id", UUID(as_uuid=True), sa.ForeignKey("maintenance_requests.id"), nullable=True),
        sa.Column("resolution_notes", sa.Text, nullable=True),
        sa.Column("resolved_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        *ts_cols(),
    )
    op.create_index("ix_grievances_grievance_code", "grievances", ["grievance_code"])
    op.create_index("ix_grievances_asset_id", "grievances", ["asset_id"])

    op.create_table(
        "tenders",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tender_number", sa.String(50), unique=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("status", _enum(TenderStatus, "tender_status"), nullable=False, server_default=TenderStatus.DRAFT.value),
        sa.Column("asset_id", UUID(as_uuid=True), sa.ForeignKey("assets.id"), nullable=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("department_id", UUID(as_uuid=True), sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("administrative_unit_id", UUID(as_uuid=True), sa.ForeignKey("administrative_units.id"), nullable=False),
        sa.Column("estimated_value", sa.Numeric(16, 2), nullable=True),
        sa.Column("emd_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("published_date", sa.Date, nullable=True),
        sa.Column("submission_deadline", sa.Date, nullable=True),
        sa.Column("awarded_bid_id", UUID(as_uuid=True), nullable=True),
        sa.Column("awarded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        *ts_cols(),
    )
    op.create_index("ix_tenders_tender_number", "tenders", ["tender_number"])

    op.create_table(
        "tender_bids",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tender_id", UUID(as_uuid=True), sa.ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("contractor_id", UUID(as_uuid=True), sa.ForeignKey("contractors.id"), nullable=False),
        sa.Column("bid_amount", sa.Numeric(16, 2), nullable=False),
        sa.Column("remarks", sa.Text, nullable=True),
        sa.Column("status", _enum(TenderBidStatus, "tender_bid_status"), nullable=False, server_default=TenderBidStatus.SUBMITTED.value),
        *ts_cols(),
    )

    op.create_foreign_key(
        "fk_tenders_awarded_bid_id", "tenders", "tender_bids", ["awarded_bid_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_tenders_awarded_bid_id", "tenders", type_="foreignkey")
    op.drop_table("tender_bids")
    op.drop_table("tenders")
    op.drop_table("grievances")

    for enum_name in ["grievance_category", "grievance_status", "tender_status", "tender_bid_status"]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
