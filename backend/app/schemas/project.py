from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import ProjectStatus
from app.schemas.common import ORMModel


class ProjectCreate(BaseModel):
    project_code: str
    name: str
    description: str | None = None
    department_id: UUID
    administrative_unit_id: UUID
    sanctioned_budget: float | None = None
    sanction_date: date | None = None
    start_date: date | None = None
    expected_completion_date: date | None = None
    contractor_id: UUID | None = None


class ProjectUpdate(BaseModel):
    status: ProjectStatus | None = None
    actual_expenditure: float | None = None
    actual_completion_date: date | None = None
    contractor_id: UUID | None = None


class ProjectRead(ORMModel):
    id: UUID
    project_code: str
    name: str
    description: str | None = None
    status: ProjectStatus
    department_id: UUID
    administrative_unit_id: UUID
    sanctioned_budget: float | None = None
    actual_expenditure: float | None = None
    sanction_date: date | None = None
    start_date: date | None = None
    expected_completion_date: date | None = None
    actual_completion_date: date | None = None
    contractor_id: UUID | None = None


class ProjectAssetLink(BaseModel):
    asset_id: UUID
