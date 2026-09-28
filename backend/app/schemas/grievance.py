from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import FindingSeverity, GrievanceCategory, GrievanceStatus
from app.schemas.common import ORMModel


class GrievanceCreate(BaseModel):
    """Public filing form — no auth required. `asset_id` is optional since a
    citizen may not know which asset a defect belongs to."""

    title: str
    description: str
    category: GrievanceCategory = GrievanceCategory.OTHER
    severity: FindingSeverity = FindingSeverity.LOW
    location: dict[str, Any] = Field(..., description="GeoJSON Point {type, coordinates}")
    asset_id: UUID | None = None
    reporter_name: str | None = None
    reporter_contact: str | None = None


class GrievanceStatusUpdate(BaseModel):
    status: GrievanceStatus
    notes: str | None = None


class GrievanceAssign(BaseModel):
    assigned_to: UUID


class GrievanceLinkAsset(BaseModel):
    asset_id: UUID


class GrievanceRead(ORMModel):
    id: UUID
    grievance_code: str
    title: str
    description: str
    category: GrievanceCategory
    severity: FindingSeverity
    status: GrievanceStatus
    location: dict[str, Any]
    asset_id: UUID | None = None
    has_photo: bool = False
    reporter_name: str | None = None
    reporter_contact: str | None = None
    assigned_to: UUID | None = None
    linked_maintenance_request_id: UUID | None = None
    resolution_notes: str | None = None
    resolved_by: UUID | None = None
    resolved_at: datetime | None = None
    created_at: datetime
