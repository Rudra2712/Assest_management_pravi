"""Jurisdiction scoping: restricts which administrative units (and therefore
which assets/tasks) a user's role grants let them see, using the
AdministrativeUnit.path materialized-path column for a cheap prefix match
instead of a recursive CTE on every request."""

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.enums import SystemRole
from app.models.geo import AdministrativeUnit
from app.models.user import User
from app.permissions.rbac import JURISDICTION_WIDE_ROLES


def user_role_codes(user: User) -> set[str]:
    return {grant.role.code for grant in user.role_grants}


def has_jurisdiction_wide_access(user: User) -> bool:
    codes = user_role_codes(user)
    return any(role.value in codes for role in JURISDICTION_WIDE_ROLES)


def jurisdiction_unit_ids(db: Session, user: User) -> list[str] | None:
    """Returns the administrative_unit ids this user's role grants scope them
    to, or None meaning unrestricted (state/department admin)."""

    if has_jurisdiction_wide_access(user):
        return None

    root_unit_ids: set[str] = set()
    for grant in user.role_grants:
        unit_id = grant.jurisdiction_unit_id or user.administrative_unit_id
        if unit_id:
            root_unit_ids.add(str(unit_id))

    if not root_unit_ids:
        return []

    roots = db.query(AdministrativeUnit).filter(AdministrativeUnit.id.in_(root_unit_ids)).all()
    if not roots:
        return []

    conditions = []
    for root in roots:
        prefix = f"{root.path}.%" if root.path else f"{root.id}.%"
        conditions.append(AdministrativeUnit.path == root.path)
        conditions.append(AdministrativeUnit.path.like(prefix))

    subtree = db.query(AdministrativeUnit.id).filter(or_(*conditions)).all()
    return [str(row[0]) for row in subtree] or [str(u) for u in root_unit_ids]


def apply_jurisdiction_filter(query, db: Session, user: User, administrative_unit_id_column):
    unit_ids = jurisdiction_unit_ids(db, user)
    if unit_ids is None:
        return query
    return query.filter(administrative_unit_id_column.in_(unit_ids))
