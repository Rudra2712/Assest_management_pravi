from uuid import UUID

from pydantic import BaseModel

from app.models.enums import AdminUnitLevel
from app.schemas.common import ORMModel


class DepartmentCreate(BaseModel):
    code: str
    name: str
    description: str | None = None


class DepartmentRead(ORMModel):
    id: UUID
    code: str
    name: str
    description: str | None = None


class AdministrativeUnitCreate(BaseModel):
    code: str
    name: str
    level: AdminUnitLevel
    parent_id: UUID | None = None


class AdministrativeUnitRead(ORMModel):
    id: UUID
    code: str
    name: str
    level: AdminUnitLevel
    parent_id: UUID | None = None
    path: str
