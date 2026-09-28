"""Default role -> permission mapping for seed data and reference. Enforcement
itself happens via the FastAPI dependencies in app.auth.deps, which check a
user's actual granted roles (app.models.user.UserRole), never the frontend."""

from app.models.enums import SystemRole

# Coarse-grained jurisdiction-wide roles (no per-unit scoping needed to act).
JURISDICTION_WIDE_ROLES = {SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN, SystemRole.AUDITOR}

# Roles restricted to their assigned administrative-unit subtree.
JURISDICTION_SCOPED_ROLES = {
    SystemRole.CIRCLE_DIVISION_OFFICER,
    SystemRole.SUB_DIVISION_OFFICER,
    SystemRole.FIELD_ENGINEER,
    SystemRole.MAINTENANCE_OFFICER,
}

READ_ONLY_ROLES = {SystemRole.AUDITOR}

# Roles allowed to approve inspections / maintenance requests / lifecycle transitions.
APPROVER_ROLES = {
    SystemRole.STATE_ADMIN,
    SystemRole.DEPARTMENT_ADMIN,
    SystemRole.CIRCLE_DIVISION_OFFICER,
    SystemRole.SUB_DIVISION_OFFICER,
}

# Roles allowed to create/edit the asset registry.
ASSET_WRITE_ROLES = {
    SystemRole.STATE_ADMIN,
    SystemRole.DEPARTMENT_ADMIN,
    SystemRole.CIRCLE_DIVISION_OFFICER,
    SystemRole.SUB_DIVISION_OFFICER,
}

# Roles allowed to perform field inspections.
INSPECTOR_ROLES = {SystemRole.FIELD_ENGINEER, SystemRole.SUB_DIVISION_OFFICER}

# Roles allowed to manage maintenance/work orders.
MAINTENANCE_ROLES = {
    SystemRole.MAINTENANCE_OFFICER,
    SystemRole.SUB_DIVISION_OFFICER,
    SystemRole.CIRCLE_DIVISION_OFFICER,
}

ADMIN_ROLES = {SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN}
