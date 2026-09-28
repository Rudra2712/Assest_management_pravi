from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import MaintenancePriority, MaintenanceRequestStatus, MaintenanceType, WorkOrderStatus
from app.schemas.common import ORMModel


class MaintenanceRequestCreate(BaseModel):
    asset_id: UUID
    source_inspection_finding_id: UUID | None = None
    maintenance_type: MaintenanceType
    priority: MaintenancePriority = MaintenancePriority.MEDIUM
    description: str
    estimated_cost: float | None = None
    due_date: date | None = None


class MaintenanceRequestDecision(BaseModel):
    approve: bool
    comments: str | None = None


class MaintenanceRequestRead(ORMModel):
    id: UUID
    asset_id: UUID
    source_inspection_finding_id: UUID | None = None
    maintenance_type: MaintenanceType
    priority: MaintenancePriority
    description: str
    estimated_cost: float | None = None
    due_date: date | None = None
    status: MaintenanceRequestStatus
    requested_by: UUID
    approved_by: UUID | None = None


class WorkOrderCreate(BaseModel):
    contractor_id: UUID | None = None
    assigned_officer_id: UUID | None = None
    priority: MaintenancePriority = MaintenancePriority.MEDIUM
    sla_due_date: date | None = None
    estimated_cost: float | None = None


class WorkOrderAssign(BaseModel):
    contractor_id: UUID | None = None
    assigned_officer_id: UUID | None = None


class WorkOrderComplete(BaseModel):
    actual_cost: float | None = None
    completion_remarks: str | None = None
    before_photo_document_ids: list[str] | None = None
    after_photo_document_ids: list[str] | None = None


class WorkOrderVerify(BaseModel):
    verified: bool
    comments: str | None = None


class WorkOrderRead(ORMModel):
    id: UUID
    work_order_code: str
    maintenance_request_id: UUID
    asset_id: UUID
    contractor_id: UUID | None = None
    assigned_officer_id: UUID | None = None
    priority: MaintenancePriority
    status: WorkOrderStatus
    sla_due_date: date | None = None
    estimated_cost: float | None = None
    actual_cost: float | None = None
    completed_at: date | None = None
    completion_remarks: str | None = None
    before_photo_document_ids: list[str] | None = None
    after_photo_document_ids: list[str] | None = None
    verified_by: UUID | None = None
    verified_at: date | None = None
