from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import ORMModel


class ContractorCreate(BaseModel):
    name: str
    registration_number: str | None = None
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None


class ContractorRead(ORMModel):
    id: UUID
    name: str
    registration_number: str | None = None
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    is_active: bool
