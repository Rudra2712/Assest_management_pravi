from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import ConditionRating, FindingSeverity, InspectionStatus
from app.schemas.common import ORMModel


class InspectionAssign(BaseModel):
    asset_id: UUID
    inspector_id: UUID
    template_id: UUID | None = None
    assigned_date: date | None = None


class InspectionFindingCreate(BaseModel):
    description: str
    severity: FindingSeverity = FindingSeverity.LOW
    photo_document_ids: list[str] | None = None
    recommends_maintenance: bool = False


class InspectionSubmit(BaseModel):
    inspection_date: date
    gps_lat: float | None = None
    gps_lon: float | None = None
    checklist_responses: dict[str, Any] | None = None
    overall_condition: ConditionRating
    remarks: str | None = None
    findings: list[InspectionFindingCreate] = []


class InspectionReview(BaseModel):
    approve: bool
    comments: str | None = None


class InspectionFindingRead(ORMModel):
    id: UUID
    description: str
    severity: FindingSeverity
    photo_document_ids: list[str] | None = None
    recommends_maintenance: bool


class InspectionRead(ORMModel):
    id: UUID
    asset_id: UUID
    inspector_id: UUID
    assigned_date: date | None = None
    inspection_date: date | None = None
    overall_condition: ConditionRating | None = None
    remarks: str | None = None
    status: InspectionStatus
    reviewed_by: UUID | None = None
    reviewed_at: datetime | None = None
    review_comments: str | None = None
    findings: list[InspectionFindingRead] = []
    gps: dict[str, Any] | None = None
