"""Check data selection, scoring boundaries, and outcome leakage."""

from pathlib import Path

import pandas as pd
import pytest

from analyze import compare_groups, load_history, rank_cars


@pytest.fixture(scope="module")
def analysis():
    """Prepare the supplied history and its robust selected factors."""
    frame = load_history(Path(__file__).with_name("fleet_history.csv"))
    comparison = compare_groups(frame)
    clean = frame[frame.km_since_service <= frame.odometer_km]
    sensitivity = compare_groups(clean)
    comparison["use_in_score"] = comparison.separates & sensitivity.separates
    return frame, comparison


def test_only_robust_factors_selected(analysis):
    frame, comparison = analysis
    assert len(frame) == 120
    assert frame.broke_down.value_counts().to_dict() == {0: 94, 1: 26}
    assert comparison.index[comparison.use_in_score].tolist() == [
        "km_since_service", "avg_daily_km"
    ]


def test_ranking_preserves_all_cars_and_score_bounds(analysis):
    frame, comparison = analysis
    ranked = rank_cars(frame, comparison)
    assert set(ranked.car_id) == set(frame.car_id)
    assert len(ranked) == len(frame)
    assert ranked.risk_score.between(0, 100).all()
    assert ranked.risk_score.is_monotonic_decreasing
    assert ranked.reading_inconsistent.sum() == 4
    assert ranked.iloc[0].car_id == "VOS-1728"


def test_score_ignores_individual_outcome_and_unused_features(analysis):
    frame, comparison = analysis
    expected = rank_cars(frame, comparison).set_index("car_id").risk_score
    altered = frame.copy()
    altered["broke_down"] = 1 - altered.broke_down
    altered["odometer_km"] = 999999
    altered["age_years"] = 99
    altered["load_factor"] = 0
    actual = rank_cars(altered, comparison).set_index("car_id").risk_score
    pd.testing.assert_series_equal(expected, actual)


def test_score_extremes_and_monotonicity(analysis):
    _, comparison = analysis
    frame = pd.DataFrame({
        "car_id": ["low", "middle", "high"],
        "km_since_service": [0, 7500, 15000],
        "avg_daily_km": [0, 100, 200], "odometer_km": [20000] * 3,
    })
    scores = rank_cars(frame, comparison).set_index("car_id").risk_score
    assert scores["low"] == pytest.approx(0)
    assert scores["middle"] == pytest.approx(50)
    assert scores["high"] == pytest.approx(100)


def test_missing_reading_is_rejected_explicitly(tmp_path, analysis):
    frame, _ = analysis
    frame = frame.copy()
    frame.loc[0, "km_since_service"] = float("nan")
    path = tmp_path / "missing.csv"
    frame.to_csv(path, index=False)
    with pytest.raises(ValueError, match="Missing readings"):
        load_history(path)
