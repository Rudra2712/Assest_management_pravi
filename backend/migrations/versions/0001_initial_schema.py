"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
import geoalchemy2

from app.models.enums import (
    AdminUnitLevel,
    AssetTypeCode,
    GeometryKind,
    LifecycleStatus,
    ConditionRating,
    InspectionStatus,
    FindingSeverity,
    MaintenanceType,
    MaintenancePriority,
    MaintenanceRequestStatus,
    WorkOrderStatus,
    ApprovalStatus,
    ApprovalEntityType,
    ProjectStatus,
    DocumentType,
    NotificationEvent,
)

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _enum(pyenum, name):
    return sa.Enum(pyenum, name=name)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    ts_cols = lambda: [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]

    op.create_table(
        "departments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        *ts_cols(),
    )

    op.create_table(
        "administrative_units",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("level", _enum(AdminUnitLevel, "admin_unit_level"), nullable=False),
        sa.Column("parent_id", UUID(as_uuid=True), sa.ForeignKey("administrative_units.id"), nullable=True),
        sa.Column("path", sa.String(1000), nullable=False, server_default=""),
        *ts_cols(),
    )
    op.create_index("ix_administrative_units_path", "administrative_units", ["path"])

    op.create_table(
        "permissions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        *ts_cols(),
    )

    op.create_table(
        "roles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("is_system_role", sa.Boolean, server_default=sa.true()),
        *ts_cols(),
    )

    op.create_table(
        "role_permissions",
        sa.Column("role_id", UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission_id", UUID(as_uuid=True), sa.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
        sa.Column("department_id", UUID(as_uuid=True), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("administrative_unit_id", UUID(as_uuid=True), sa.ForeignKey("administrative_units.id"), nullable=True),
        *ts_cols(),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "user_roles",
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("jurisdiction_unit_id", UUID(as_uuid=True), sa.ForeignKey("administrative_units.id"), nullable=True),
    )

    op.create_table(
        "asset_categories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        *ts_cols(),
    )

    op.create_table(
        "asset_types",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("code", _enum(AssetTypeCode, "asset_type_code"), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("default_geometry_kind", _enum(GeometryKind, "geometry_kind"), nullable=False),
        sa.Column("category_id", UUID(as_uuid=True), sa.ForeignKey("asset_categories.id"), nullable=True),
        *ts_cols(),
    )

    op.create_table(
        "approvals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_type", _enum(ApprovalEntityType, "approval_entity_type"), nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("submitted_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("approver_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", _enum(ApprovalStatus, "approval_status"), nullable=False, server_default=ApprovalStatus.PENDING.value),
        sa.Column("comments", sa.Text, nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        *ts_cols(),
    )
    op.create_index("ix_approvals_entity_id", "approvals", ["entity_id"])

    op.create_table(
        "contractors",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("registration_number", sa.String(100), unique=True, nullable=True),
        sa.Column("contact_person", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        *ts_cols(),
    )

    op.create_table(
        "projects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_code", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", _enum(ProjectStatus, "project_status"), nullable=False, server_default=ProjectStatus.PROPOSED.value),
        sa.Column("department_id", UUID(as_uuid=True), sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("administrative_unit_id", UUID(as_uuid=True), sa.ForeignKey("administrative_units.id"), nullable=False),
        sa.Column("sanctioned_budget", sa.Numeric(16, 2), nullable=True),
        sa.Column("actual_expenditure", sa.Numeric(16, 2), nullable=True),
        sa.Column("sanction_date", sa.Date, nullable=True),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("expected_completion_date", sa.Date, nullable=True),
        sa.Column("actual_completion_date", sa.Date, nullable=True),
        sa.Column("contractor_id", UUID(as_uuid=True), sa.ForeignKey("contractors.id"), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        *ts_cols(),
    )

    op.create_table(
        "assets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_code", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("asset_type_id", UUID(as_uuid=True), sa.ForeignKey("asset_types.id"), nullable=False),
        sa.Column("category_id", UUID(as_uuid=True), sa.ForeignKey("asset_categories.id"), nullable=True),
        sa.Column("ownership", sa.String(255), nullable=True),
        sa.Column("department_id", UUID(as_uuid=True), sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("administrative_unit_id", UUID(as_uuid=True), sa.ForeignKey("administrative_units.id"), nullable=False),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("acquisition_date", sa.Date, nullable=True),
        sa.Column("commissioning_date", sa.Date, nullable=True),
        sa.Column("lifecycle_status", _enum(LifecycleStatus, "lifecycle_status"), nullable=False, server_default=LifecycleStatus.PLANNED.value),
        sa.Column("current_condition", _enum(ConditionRating, "condition_rating"), nullable=True),
        sa.Column("original_cost", sa.Numeric(16, 2), nullable=True),
        sa.Column("current_value", sa.Numeric(16, 2), nullable=True),
        sa.Column("useful_life_years", sa.Integer, nullable=True),
        sa.Column("expected_end_of_life", sa.Date, nullable=True),
        sa.Column("responsible_officer_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("linked_project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("is_deleted", sa.Boolean, server_default=sa.false(), nullable=False),
        *ts_cols(),
    )
    op.create_index("ix_assets_asset_code", "assets", ["asset_code"])
    op.create_index("ix_assets_administrative_unit_id", "assets", ["administrative_unit_id"])

    op.create_table(
        "asset_geometries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("geometry_kind", _enum(GeometryKind, "geometry_kind_geom"), nullable=False),
        sa.Column("geom", geoalchemy2.Geometry(geometry_type="GEOMETRY", srid=4326), nullable=False),
        *ts_cols(),
    )
    # GeoAlchemy2 auto-creates a GIST spatial index for this column (spatial_index=True
    # is the type's default) — no explicit op.create_index needed here.

    op.create_table(
        "asset_relationships",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("parent_asset_id", UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("child_asset_id", UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relationship_type", sa.String(50), nullable=False, server_default="RELATED"),
        *ts_cols(),
    )

    op.create_table(
        "roads",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("length_km", sa.Numeric(10, 3), nullable=True),
        sa.Column("width_m", sa.Numeric(6, 2), nullable=True),
        sa.Column("number_of_lanes", sa.Integer, nullable=True),
        sa.Column("surface_type", sa.String(100), nullable=True),
        sa.Column("start_point_desc", sa.String(255), nullable=True),
        sa.Column("end_point_desc", sa.String(255), nullable=True),
        sa.Column("traffic_info", sa.String(500), nullable=True),
        *ts_cols(),
    )

    op.create_table(
        "bridges",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("length_m", sa.Numeric(10, 2), nullable=True),
        sa.Column("width_m", sa.Numeric(6, 2), nullable=True),
        sa.Column("number_of_spans", sa.Integer, nullable=True),
        sa.Column("bridge_type", sa.String(100), nullable=True),
        sa.Column("material", sa.String(100), nullable=True),
        sa.Column("load_capacity_tonnes", sa.Numeric(8, 2), nullable=True),
        *ts_cols(),
    )

    op.create_table(
        "culverts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("culvert_type", sa.String(100), nullable=True),
        sa.Column("length_m", sa.Numeric(8, 2), nullable=True),
        sa.Column("opening_width_m", sa.Numeric(6, 2), nullable=True),
        sa.Column("material", sa.String(100), nullable=True),
        *ts_cols(),
    )

    op.create_table(
        "buildings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("plot_area_sqm", sa.Numeric(10, 2), nullable=True),
        sa.Column("built_up_area_sqm", sa.Numeric(10, 2), nullable=True),
        sa.Column("number_of_floors", sa.Integer, nullable=True),
        sa.Column("construction_year", sa.Integer, nullable=True),
        sa.Column("building_type", sa.String(100), nullable=True),
        sa.Column("occupancy_use", sa.String(255), nullable=True),
        *ts_cols(),
    )

    op.create_table(
        "structures",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("structure_subtype", sa.String(100), nullable=True),
        sa.Column("attributes", JSONB, nullable=True),
        *ts_cols(),
    )

    op.create_table(
        "project_assets",
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("asset_id", UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "lifecycle_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("old_status", _enum(LifecycleStatus, "lifecycle_status"), nullable=True),
        sa.Column("new_status", _enum(LifecycleStatus, "lifecycle_status"), nullable=False),
        sa.Column("changed_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("approval_id", UUID(as_uuid=True), sa.ForeignKey("approvals.id"), nullable=True),
        *ts_cols(),
    )
    op.create_index("ix_lifecycle_events_asset_id", "lifecycle_events", ["asset_id"])

    op.create_table(
        "inspection_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_type_id", UUID(as_uuid=True), sa.ForeignKey("asset_types.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
        *ts_cols(),
    )

    op.create_table(
        "inspection_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("template_id", UUID(as_uuid=True), sa.ForeignKey("inspection_templates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sequence", sa.Integer, server_default="0"),
        sa.Column("question", sa.String(500), nullable=False),
        sa.Column("response_type", sa.String(20), server_default="RATING"),
        sa.Column("weight", sa.Numeric(5, 2), server_default="1.0"),
        *ts_cols(),
    )

    op.create_table(
        "inspections",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("template_id", UUID(as_uuid=True), sa.ForeignKey("inspection_templates.id"), nullable=True),
        sa.Column("inspector_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assigned_date", sa.Date, nullable=True),
        sa.Column("inspection_date", sa.Date, nullable=True),
        sa.Column("gps_point", geoalchemy2.Geometry(geometry_type="POINT", srid=4326), nullable=True),
        sa.Column("checklist_responses", JSONB, nullable=True),
        sa.Column("overall_condition", _enum(ConditionRating, "condition_rating"), nullable=True),
        sa.Column("remarks", sa.Text, nullable=True),
        sa.Column("status", _enum(InspectionStatus, "inspection_status"), nullable=False, server_default=InspectionStatus.ASSIGNED.value),
        sa.Column("reviewed_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_comments", sa.Text, nullable=True),
        *ts_cols(),
    )
    op.create_index("ix_inspections_asset_id", "inspections", ["asset_id"])

    op.create_table(
        "inspection_findings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("inspection_id", UUID(as_uuid=True), sa.ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("severity", _enum(FindingSeverity, "finding_severity"), nullable=False, server_default=FindingSeverity.LOW.value),
        sa.Column("photo_document_ids", JSONB, nullable=True),
        sa.Column("recommends_maintenance", sa.Boolean, server_default=sa.false()),
        *ts_cols(),
    )

    op.create_table(
        "condition_assessments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("inspection_id", UUID(as_uuid=True), sa.ForeignKey("inspections.id"), nullable=True),
        sa.Column("factor_inputs", JSONB, nullable=False),
        sa.Column("factor_weights", JSONB, nullable=False),
        sa.Column("condition_score", sa.Numeric(6, 3), nullable=False),
        sa.Column("condition_rating", _enum(ConditionRating, "condition_rating"), nullable=False),
        sa.Column("risk_probability", sa.Numeric(5, 4), nullable=True),
        sa.Column("risk_impact", sa.Numeric(5, 4), nullable=True),
        sa.Column("risk_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("assessed_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        *ts_cols(),
    )
    op.create_index("ix_condition_assessments_asset_id", "condition_assessments", ["asset_id"])

    op.create_table(
        "maintenance_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_inspection_finding_id", UUID(as_uuid=True), sa.ForeignKey("inspection_findings.id"), nullable=True),
        sa.Column("maintenance_type", _enum(MaintenanceType, "maintenance_type"), nullable=False),
        sa.Column("priority", _enum(MaintenancePriority, "maintenance_priority"), nullable=False, server_default=MaintenancePriority.MEDIUM.value),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("estimated_cost", sa.Numeric(14, 2), nullable=True),
        sa.Column("due_date", sa.Date, nullable=True),
        sa.Column("status", _enum(MaintenanceRequestStatus, "maintenance_request_status"), nullable=False, server_default=MaintenanceRequestStatus.OPEN.value),
        sa.Column("requested_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("approved_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        *ts_cols(),
    )
    op.create_index("ix_maintenance_requests_asset_id", "maintenance_requests", ["asset_id"])

    op.create_table(
        "work_orders",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("work_order_code", sa.String(50), unique=True, nullable=False),
        sa.Column("maintenance_request_id", UUID(as_uuid=True), sa.ForeignKey("maintenance_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_id", UUID(as_uuid=True), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("contractor_id", UUID(as_uuid=True), sa.ForeignKey("contractors.id"), nullable=True),
        sa.Column("assigned_officer_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("priority", _enum(MaintenancePriority, "maintenance_priority"), nullable=False, server_default=MaintenancePriority.MEDIUM.value),
        sa.Column("status", _enum(WorkOrderStatus, "work_order_status"), nullable=False, server_default=WorkOrderStatus.CREATED.value),
        sa.Column("sla_due_date", sa.Date, nullable=True),
        sa.Column("estimated_cost", sa.Numeric(14, 2), nullable=True),
        sa.Column("actual_cost", sa.Numeric(14, 2), nullable=True),
        sa.Column("completed_at", sa.Date, nullable=True),
        sa.Column("completion_remarks", sa.Text, nullable=True),
        sa.Column("before_photo_document_ids", JSONB, nullable=True),
        sa.Column("after_photo_document_ids", JSONB, nullable=True),
        sa.Column("verified_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("verified_at", sa.Date, nullable=True),
        *ts_cols(),
    )
    op.create_index("ix_work_orders_asset_id", "work_orders", ["asset_id"])

    op.create_table(
        "maintenance_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("work_order_id", UUID(as_uuid=True), sa.ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event", sa.String(100), nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("recorded_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        *ts_cols(),
    )

    op.create_table(
        "contractor_assignments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("contractor_id", UUID(as_uuid=True), sa.ForeignKey("contractors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("work_order_id", UUID(as_uuid=True), sa.ForeignKey("work_orders.id"), nullable=True),
        sa.Column("role_description", sa.String(255), nullable=True),
        *ts_cols(),
    )

    op.create_table(
        "documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("document_type", _enum(DocumentType, "document_type"), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(150), nullable=False),
        sa.Column("size_bytes", sa.BigInteger, nullable=False),
        sa.Column("storage_key", sa.String(1000), nullable=False),
        sa.Column("linked_entity_type", sa.String(50), nullable=False),
        sa.Column("linked_entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("access_roles", JSONB, nullable=True),
        sa.Column("current_version", sa.Integer, server_default="1"),
        *ts_cols(),
    )
    op.create_index("ix_documents_linked_entity_id", "documents", ["linked_entity_id"])

    op.create_table(
        "document_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("storage_key", sa.String(1000), nullable=False),
        sa.Column("size_bytes", sa.BigInteger, nullable=False),
        sa.Column("uploaded_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        *ts_cols(),
    )

    op.create_table(
        "notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("recipient_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("event", _enum(NotificationEvent, "notification_event"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text, nullable=True),
        sa.Column("context", JSONB, nullable=True),
        sa.Column("is_read", sa.Boolean, server_default=sa.false()),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("email_dispatch_requested", sa.Boolean, server_default=sa.false()),
        sa.Column("sms_dispatch_requested", sa.Boolean, server_default=sa.false()),
        *ts_cols(),
    )
    op.create_index("ix_notifications_recipient_id", "notifications", ["recipient_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("old_value", JSONB, nullable=True),
        sa.Column("new_value", JSONB, nullable=True),
        sa.Column("request_ip", INET, nullable=True),
        sa.Column("request_metadata", JSONB, nullable=True),
        *ts_cols(),
    )
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])


def downgrade() -> None:
    for table in [
        "audit_logs", "notifications", "document_versions", "documents",
        "contractor_assignments", "maintenance_records", "work_orders",
        "maintenance_requests", "condition_assessments", "inspection_findings",
        "inspections", "inspection_items", "inspection_templates",
        "lifecycle_events", "project_assets", "structures", "buildings",
        "culverts", "bridges", "roads", "asset_relationships",
        "asset_geometries", "assets", "projects", "contractors", "approvals",
        "asset_types", "asset_categories", "user_roles", "users",
        "role_permissions", "roles", "permissions", "administrative_units",
        "departments",
    ]:
        op.drop_table(table)

    for enum_name in [
        "admin_unit_level", "asset_type_code", "geometry_kind", "geometry_kind_geom",
        "lifecycle_status", "condition_rating", "inspection_status", "finding_severity",
        "maintenance_type", "maintenance_priority", "maintenance_request_status",
        "work_order_status", "approval_status", "approval_entity_type",
        "project_status", "document_type", "notification_event",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
