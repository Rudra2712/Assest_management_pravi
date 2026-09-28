"""normalize seeded demo account grants

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-29

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_DEMO_ROLE_BY_EMAIL = {
    "state.admin@rnb.gov.in": "STATE_ADMIN",
    "dept.admin@rnb.gov.in": "DEPARTMENT_ADMIN",
    "field.engineer@rnb.gov.in": "FIELD_ENGINEER",
    "maintenance.officer@rnb.gov.in": "MAINTENANCE_OFFICER",
    "contractor.user@rnb.gov.in": "CONTRACTOR",
}


def upgrade() -> None:
    connection = op.get_bind()
    for email, role_code in _DEMO_ROLE_BY_EMAIL.items():
        row = connection.execute(
            sa.text("SELECT id, administrative_unit_id FROM users WHERE email = :email"),
            {"email": email},
        ).first()
        role_id = connection.execute(
            sa.text("SELECT id FROM roles WHERE code = :code"),
            {"code": role_code},
        ).scalar_one_or_none()
        if row is None or role_id is None:
            continue

        connection.execute(
            sa.text("DELETE FROM user_roles WHERE user_id = :user_id AND role_id <> :role_id"),
            {"user_id": row.id, "role_id": role_id},
        )
        connection.execute(
            sa.text(
                "INSERT INTO user_roles (user_id, role_id, jurisdiction_unit_id) "
                "VALUES (:user_id, :role_id, :unit_id) ON CONFLICT (user_id, role_id) DO NOTHING"
            ),
            {"user_id": row.id, "role_id": role_id, "unit_id": row.administrative_unit_id},
        )


def downgrade() -> None:
    pass