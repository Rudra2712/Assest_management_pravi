import uuid

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, UUIDPKMixin, TimestampMixin
from app.models.enums import ConditionRating


class ConditionAssessment(UUIDPKMixin, TimestampMixin, Base):
    """Deterministic, explainable condition/risk score. `factor_inputs` and
    `factor_weights` are persisted so the resulting score/rating can always be
    reconstructed and audited — no black-box model."""

    __tablename__ = "condition_assessments"

    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    inspection_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("inspections.id"), nullable=True)

    factor_inputs: Mapped[dict] = mapped_column(JSONB, nullable=False)
    factor_weights: Mapped[dict] = mapped_column(JSONB, nullable=False)

    condition_score: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False)  # 0 (worst) - 100 (best)
    condition_rating: Mapped[ConditionRating] = mapped_column(nullable=False)

    risk_probability: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    risk_impact: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)

    assessed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
