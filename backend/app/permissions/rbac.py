"""Default role -> permission mapping for seed data and reference. Enforcement
itself happens via the FastAPI dependencies in app.auth.deps, which check a
user's actual granted roles (app.models.user.UserRole), never the frontend."""

from app.models.enums import SystemRole

# Coarse-grained jurisdiction-wide roles (no per-unit scoping needed to act).
JURISDICTION_WIDE_ROLES = {SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN}

# Roles restricted to their assigned administrative-unit subtree.
JURISDICTION_SCOPED_ROLES = {
    SystemRole.FIELD_ENGINEER,
    SystemRole.MAINTENANCE_OFFICER,
}

# Roles allowed to approve inspections / maintenance requests / lifecycle transitions.
APPROVER_ROLES = {
    SystemRole.STATE_ADMIN,
    SystemRole.DEPARTMENT_ADMIN,
}

# Roles allowed to create/edit the asset registry.
ASSET_WRITE_ROLES = {
    SystemRole.STATE_ADMIN,
    SystemRole.DEPARTMENT_ADMIN,
}

# Roles allowed to perform field inspections.
INSPECTOR_ROLES = {SystemRole.FIELD_ENGINEER}

# Roles allowed to manage maintenance/work orders.
MAINTENANCE_ROLES = {
    SystemRole.MAINTENANCE_OFFICER,
}

ADMIN_ROLES = {SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN}
