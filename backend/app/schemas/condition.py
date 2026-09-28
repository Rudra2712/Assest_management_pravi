from datetime import datetime
from uuid import UUID

from app.models.enums import ConditionRating
from app.schemas.common import ORMModel


class ConditionAssessmentRead(ORMModel):
    id: UUID
    asset_id: UUID
    inspection_id: UUID | None = None
    factor_inputs: dict
    factor_weights: dict
    condition_score: float
    condition_rating: ConditionRating
    risk_probability: float | None = None
    risk_impact: float | None = None
    risk_score: float | None = None
    created_at: datetime
