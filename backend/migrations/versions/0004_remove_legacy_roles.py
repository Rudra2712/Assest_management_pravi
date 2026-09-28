"""retire circle, subdivision and auditor roles

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-29

"""
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_RETIRED_ROLES = ["CIRCLE_DIVISION_OFFICER", "SUB_DIVISION_OFFICER", "AUDITOR"]
_RETIRED_EMAILS = [
    "circle.north@rnb.gov.in",
    "subdivision.n1a@rnb.gov.in",
    "auditor@rnb.gov.in",
]


def upgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text("UPDATE users SET is_active = FALSE WHERE email IN :emails")
        .bindparams(sa.bindparam("emails", expanding=True)),
        {"emails": _RETIRED_EMAILS},
    )
    for table_name in ("role_permissions", "user_roles"):
        connection.execute(
            sa.text(f"DELETE FROM {table_name} WHERE role_id IN (SELECT id FROM roles WHERE code IN :roles)")
            .bindparams(sa.bindparam("roles", expanding=True)),
            {"roles": _RETIRED_ROLES},
        )
    connection.execute(
        sa.text("DELETE FROM roles WHERE code IN :roles")
        .bindparams(sa.bindparam("roles", expanding=True)),
        {"roles": _RETIRED_ROLES},
    )


def downgrade() -> None:
    roles = sa.table(
        "roles",
        sa.column("id", UUID(as_uuid=True)),
        sa.column("code", sa.String(50)),
        sa.column("name", sa.String(100)),
        sa.column("is_system_role", sa.Boolean),
    )
    op.bulk_insert(roles, [
        {"id": uuid.uuid4(), "code": "CIRCLE_DIVISION_OFFICER", "name": "Circle Division Officer", "is_system_role": True},
        {"id": uuid.uuid4(), "code": "SUB_DIVISION_OFFICER", "name": "Sub Division Officer", "is_system_role": True},
        {"id": uuid.uuid4(), "code": "AUDITOR", "name": "Auditor", "is_system_role": True},
    ])