from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.schemas.common import ORMModel


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class RoleGrantRead(ORMModel):
    role_code: str
    role_name: str
    jurisdiction_unit_id: UUID | None = None


class CurrentUserRead(ORMModel):
    id: UUID
    email: str
    full_name: str
    phone: str | None = None
    department_id: UUID | None = None
    administrative_unit_id: UUID | None = None
    roles: list[str] = []
