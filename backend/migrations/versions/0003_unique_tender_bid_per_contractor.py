"""one bid per contractor per tender

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-29

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_tender_bid_contractor",
        "tender_bids",
        ["tender_id", "contractor_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_tender_bid_contractor", "tender_bids", type_="unique")