from datetime import date, timedelta
from types import SimpleNamespace

from app.models.enums import ConditionRating, FindingSeverity
from app.services.condition_service import compute_condition, score_to_rating


def make_asset(**overrides):
    defaults = dict(
        commissioning_date=date.today() - timedelta(days=365 * 5),
        useful_life_years=25,
        expected_end_of_life=date.today() + timedelta(days=365 * 20),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_score_to_rating_thresholds():
    assert score_to_rating(95) == ConditionRating.GOOD
    assert score_to_rating(80) == ConditionRating.GOOD
    assert score_to_rating(79.9) == ConditionRating.FAIR
    assert score_to_rating(60) == ConditionRating.FAIR
    assert score_to_rating(59.9) == ConditionRating.POOR
    assert score_to_rating(35) == ConditionRating.POOR
    assert score_to_rating(10) == ConditionRating.CRITICAL


def test_new_asset_with_no_inspection_scores_reasonably_well():
    asset = make_asset()
    result = compute_condition(asset, inspection=None, open_maintenance_request_count=0, criticality=0.5)

    assert result["condition_score"] > 60
    assert set(result["factor_inputs"].keys()) == {"age", "inspection_condition", "defect_severity", "maintenance_history", "eol_proximity"}
    assert result["factor_weights"] == {
        "age": 0.20, "inspection_condition": 0.30, "defect_severity": 0.25, "maintenance_history": 0.15, "eol_proximity": 0.10,
    }


def test_critical_inspection_finding_drags_score_down():
    asset = make_asset()
    inspection = SimpleNamespace(
        overall_condition=ConditionRating.CRITICAL,
        findings=[SimpleNamespace(severity=FindingSeverity.CRITICAL)],
    )
    result = compute_condition(asset, inspection=inspection, open_maintenance_request_count=2, criticality=0.9)

    assert result["condition_rating"] in (ConditionRating.POOR, ConditionRating.CRITICAL)
    assert result["risk_score"] > 0


def test_asset_past_end_of_life_has_zero_eol_factor():
    asset = make_asset(expected_end_of_life=date.today() - timedelta(days=1))
    result = compute_condition(asset)
    assert result["factor_inputs"]["eol_proximity"] == 0.0


def test_score_is_deterministic_for_same_inputs():
    asset = make_asset()
    result_a = compute_condition(asset, criticality=0.4)
    result_b = compute_condition(asset, criticality=0.4)
    assert result_a == result_b
