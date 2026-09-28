"""Deterministic, explainable condition/risk scoring for MVP.

Every factor and its weight is persisted alongside the result
(app.models.condition.ConditionAssessment.factor_inputs / factor_weights) so
the score can always be reconstructed and audited. No opaque ML model.
"""

from datetime import date

from app.models.asset import Asset
from app.models.enums import ConditionRating, FindingSeverity
from app.models.inspection import Inspection

WEIGHTS = {
    "age": 0.20,
    "inspection_condition": 0.30,
    "defect_severity": 0.25,
    "maintenance_history": 0.15,
    "eol_proximity": 0.10,
}

_CONDITION_SCORE = {
    ConditionRating.GOOD: 1.0,
    ConditionRating.FAIR: 0.7,
    ConditionRating.POOR: 0.4,
    ConditionRating.CRITICAL: 0.1,
}

_SEVERITY_SCORE = {
    FindingSeverity.LOW: 0.9,
    FindingSeverity.MEDIUM: 0.6,
    FindingSeverity.HIGH: 0.3,
    FindingSeverity.CRITICAL: 0.0,
}


def _age_factor(asset: Asset) -> float:
    if not asset.commissioning_date or not asset.useful_life_years:
        return 0.7  # neutral default when data is incomplete
    age_years = (date.today() - asset.commissioning_date).days / 365.25
    ratio = min(max(age_years / asset.useful_life_years, 0.0), 1.0)
    return round(1.0 - ratio, 4)


def _eol_proximity_factor(asset: Asset) -> float:
    if not asset.expected_end_of_life:
        return 0.7
    days_remaining = (asset.expected_end_of_life - date.today()).days
    if days_remaining <= 0:
        return 0.0
    return round(min(days_remaining / (5 * 365.25), 1.0), 4)


def _inspection_condition_factor(inspection: Inspection | None) -> float:
    if inspection is None or inspection.overall_condition is None:
        return 0.7
    return _CONDITION_SCORE[inspection.overall_condition]


def _defect_severity_factor(inspection: Inspection | None) -> float:
    if inspection is None or not inspection.findings:
        return 1.0
    worst = min((_SEVERITY_SCORE[f.severity] for f in inspection.findings), default=1.0)
    return worst


def _maintenance_history_factor(open_maintenance_request_count: int) -> float:
    if open_maintenance_request_count <= 0:
        return 1.0
    return round(max(1.0 - 0.25 * open_maintenance_request_count, 0.0), 4)


def score_to_rating(score: float) -> ConditionRating:
    if score >= 80:
        return ConditionRating.GOOD
    if score >= 60:
        return ConditionRating.FAIR
    if score >= 35:
        return ConditionRating.POOR
    return ConditionRating.CRITICAL


def compute_condition(
    asset: Asset,
    inspection: Inspection | None = None,
    open_maintenance_request_count: int = 0,
    criticality: float = 0.5,
) -> dict:
    inputs = {
        "age": _age_factor(asset),
        "inspection_condition": _inspection_condition_factor(inspection),
        "defect_severity": _defect_severity_factor(inspection),
        "maintenance_history": _maintenance_history_factor(open_maintenance_request_count),
        "eol_proximity": _eol_proximity_factor(asset),
    }

    weighted_sum = sum(inputs[k] * WEIGHTS[k] for k in WEIGHTS)
    score = round(weighted_sum * 100, 3)
    rating = score_to_rating(score)

    risk_probability = round(1 - weighted_sum, 4)
    risk_impact = round(criticality, 4)
    risk_score = round(risk_probability * risk_impact, 4)

    return {
        "factor_inputs": inputs,
        "factor_weights": WEIGHTS,
        "condition_score": score,
        "condition_rating": rating,
        "risk_probability": risk_probability,
        "risk_impact": risk_impact,
        "risk_score": risk_score,
    }
