from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.enums import TenderBidStatus, TenderStatus
from app.schemas.common import ORMModel


class TenderCreate(BaseModel):
    title: str
    description: str
    department_id: UUID
    administrative_unit_id: UUID
    asset_id: UUID | None = None
    project_id: UUID | None = None
    estimated_value: float | None = Field(default=None, gt=0)
    emd_amount: float | None = Field(default=None, ge=0)
    submission_deadline: date | None = None

    @field_validator("submission_deadline")
    @classmethod
    def deadline_must_not_be_past(cls, value: date | None) -> date | None:
        if value is not None and value < date.today():
            raise ValueError("Submission deadline cannot be in the past")
        return value


class TenderBidCreate(BaseModel):
    bid_amount: float = Field(gt=0)
    remarks: str | None = None


class TenderBidRead(ORMModel):
    id: UUID
    tender_id: UUID
    contractor_id: UUID
    contractor_name: str | None = None
    bid_amount: float
    remarks: str | None = None
    status: TenderBidStatus
    created_at: datetime


class TenderAward(BaseModel):
    bid_id: UUID


class TenderRead(ORMModel):
    id: UUID
    tender_number: str
    title: str
    description: str
    status: TenderStatus
    asset_id: UUID | None = None
    project_id: UUID | None = None
    department_id: UUID
    administrative_unit_id: UUID
    estimated_value: float | None = None
    emd_amount: float | None = None
    published_date: date | None = None
    submission_deadline: date | None = None
    awarded_bid_id: UUID | None = None
    awarded_at: datetime | None = None
    bid_count: int = 0
    bids: list[TenderBidRead] = Field(default_factory=list)
