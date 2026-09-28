from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.schemas.common import ORMModel


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    phone: str | None = None
    department_id: UUID | None = None
    administrative_unit_id: UUID | None = None
    role_codes: list[str] = []


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    is_active: bool | None = None
    department_id: UUID | None = None
    administrative_unit_id: UUID | None = None


class RoleAssign(BaseModel):
    role_code: str
    jurisdiction_unit_id: UUID | None = None


class UserRead(ORMModel):
    id: UUID
    email: str
    full_name: str
    phone: str | None = None
    is_active: bool
    department_id: UUID | None = None
    administrative_unit_id: UUID | None = None
    roles: list[str] = []
