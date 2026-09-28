from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.asset import Asset, AssetType
from app.models.enums import ConditionRating, InspectionStatus, ProjectStatus, WorkOrderStatus
from app.models.geo import AdministrativeUnit
from app.models.inspection import Inspection
from app.models.maintenance import WorkOrder
from app.models.project import Project
from app.models.user import User
from app.permissions.jurisdiction import apply_jurisdiction_filter

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    asset_query = apply_jurisdiction_filter(
        db.query(Asset).filter(Asset.is_deleted.is_(False)), db, user, Asset.administrative_unit_id
    )
    asset_ids_subq = asset_query.with_entities(Asset.id).subquery()

    total_assets = asset_query.count()

    by_type_rows = (
        db.query(AssetType.code, func.count(Asset.id))
        .join(Asset, Asset.asset_type_id == AssetType.id)
        .filter(Asset.id.in_(db.query(asset_ids_subq.c.id)))
        .group_by(AssetType.code)
        .all()
    )
    by_type = {code.value: count for code, count in by_type_rows}

    by_lifecycle_rows = (
        db.query(Asset.lifecycle_status, func.count(Asset.id))
        .filter(Asset.id.in_(db.query(asset_ids_subq.c.id)))
        .group_by(Asset.lifecycle_status)
        .all()
    )
    by_lifecycle = {status.value: count for status, count in by_lifecycle_rows}

    by_condition_rows = (
        db.query(Asset.current_condition, func.count(Asset.id))
        .filter(Asset.id.in_(db.query(asset_ids_subq.c.id)))
        .group_by(Asset.current_condition)
        .all()
    )
    by_condition = {(cond.value if cond else "UNASSESSED"): count for cond, count in by_condition_rows}

    critical_assets = asset_query.filter(Asset.current_condition == ConditionRating.CRITICAL).count()

    by_admin_unit_rows = (
        db.query(AdministrativeUnit.name, func.count(Asset.id))
        .join(Asset, Asset.administrative_unit_id == AdministrativeUnit.id)
        .filter(Asset.id.in_(db.query(asset_ids_subq.c.id)))
        .group_by(AdministrativeUnit.name)
        .all()
    )
    by_admin_unit = {name: count for name, count in by_admin_unit_rows}

    total_asset_value = asset_query.with_entities(func.coalesce(func.sum(Asset.current_value), 0)).scalar()

    # "Due" is computed on demand rather than via a background scheduler (no Celery/Redis for MVP).
    today = date.today()
    soon = today + timedelta(days=7)

    inspections_due_soon = (
        db.query(Inspection)
        .filter(Inspection.status.in_([InspectionStatus.ASSIGNED, InspectionStatus.IN_PROGRESS]))
        .filter(Inspection.assigned_date.isnot(None), Inspection.assigned_date <= soon)
        .count()
    )
    inspections_overdue = (
        db.query(Inspection)
        .filter(Inspection.status.in_([InspectionStatus.ASSIGNED, InspectionStatus.IN_PROGRESS]))
        .filter(Inspection.assigned_date.isnot(None), Inspection.assigned_date < today)
        .count()
    )

    maintenance_due_soon = (
        db.query(WorkOrder)
        .filter(WorkOrder.status.notin_([WorkOrderStatus.CLOSED, WorkOrderStatus.CANCELLED]))
        .filter(WorkOrder.sla_due_date.isnot(None), WorkOrder.sla_due_date <= soon)
        .count()
    )
    overdue_work_orders = (
        db.query(WorkOrder)
        .filter(WorkOrder.status.notin_([WorkOrderStatus.CLOSED, WorkOrderStatus.CANCELLED, WorkOrderStatus.VERIFIED]))
        .filter(WorkOrder.sla_due_date.isnot(None), WorkOrder.sla_due_date < today)
        .count()
    )
    active_maintenance = db.query(WorkOrder).filter(WorkOrder.status.in_([WorkOrderStatus.ASSIGNED, WorkOrderStatus.IN_PROGRESS])).count()
    maintenance_expenditure = db.query(func.coalesce(func.sum(WorkOrder.actual_cost), 0)).scalar()

    projects_in_progress = db.query(Project).filter(Project.status == ProjectStatus.IN_PROGRESS).count()
    projects_completed = db.query(Project).filter(Project.status == ProjectStatus.COMPLETED).count()

    return {
        "total_assets": total_assets,
        "assets_by_type": by_type,
        "assets_by_lifecycle_status": by_lifecycle,
        "assets_by_condition": by_condition,
        "assets_by_administrative_unit": by_admin_unit,
        "critical_assets": critical_assets,
        "total_asset_value": float(total_asset_value or 0),
        "inspections_due_soon": inspections_due_soon,
        "inspections_overdue": inspections_overdue,
        "maintenance_due_soon": maintenance_due_soon,
        "overdue_work_orders": overdue_work_orders,
        "active_maintenance": active_maintenance,
        "maintenance_expenditure": float(maintenance_expenditure or 0),
        "projects_in_progress": projects_in_progress,
        "projects_completed": projects_completed,
    }


@router.get("/field-dashboard")
def field_dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    today = date.today()
    my_inspections = db.query(Inspection).filter(Inspection.inspector_id == user.id)
    assigned = my_inspections.filter(Inspection.status.in_([InspectionStatus.ASSIGNED, InspectionStatus.IN_PROGRESS])).count()
    overdue = my_inspections.filter(
        Inspection.status.in_([InspectionStatus.ASSIGNED, InspectionStatus.IN_PROGRESS]),
        Inspection.assigned_date.isnot(None),
        Inspection.assigned_date < today,
    ).count()

    my_work_orders = db.query(WorkOrder).filter(WorkOrder.assigned_officer_id == user.id)
    assigned_wo = my_work_orders.filter(WorkOrder.status.in_([WorkOrderStatus.ASSIGNED, WorkOrderStatus.IN_PROGRESS])).count()

    critical_findings = (
        db.query(Inspection)
        .filter(Inspection.inspector_id == user.id, Inspection.overall_condition == ConditionRating.CRITICAL)
        .count()
    )

    return {
        "assigned_inspections": assigned,
        "overdue_inspections": overdue,
        "assigned_work_orders": assigned_wo,
        "critical_findings_reported": critical_findings,
    }
