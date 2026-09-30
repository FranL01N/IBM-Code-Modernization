# km_since_service separates breakdown groups most; avg_daily_km also shows a robust difference.
# Both survive removal of 4 inconsistent records; mileage/age do not, and load_factor is less robust.
"""Compare historical groups and build a transparent relative risk ranking."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

FEATURES = [
    "odometer_km", "km_since_service", "avg_daily_km", "load_factor", "age_years"
]
PERMUTATIONS = 10_000
SEED = 42
MIN_EFFECT = 0.5
MAX_P = 0.05


def load_history(path: Path) -> pd.DataFrame:
    """Load complete, finite observations with unique IDs and binary outcomes."""
    frame = pd.read_csv(path)
    required = ["car_id", *FEATURES, "broke_down"]
    missing = set(required) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if frame[required].isna().any().any():
        raise ValueError("Missing readings must be resolved before scoring.")
    if frame["car_id"].duplicated().any():
        raise ValueError("Each car_id must identify exactly one car.")
    if set(frame["broke_down"].unique()) != {0, 1}:
        raise ValueError("broke_down must contain both groups, coded 0 and 1.")
    for column in [*FEATURES, "broke_down"]:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    if not np.isfinite(frame[FEATURES].to_numpy()).all():
        raise ValueError("Readings must be finite numbers.")
    if (frame[FEATURES] < 0).any().any() or (frame["load_factor"] > 1).any():
        raise ValueError("Readings must be nonnegative and load_factor at most 1.")
    if frame.groupby("broke_down").size().min() < 2:
        raise ValueError("At least two observations per group are needed.")
    return frame


def compare_groups(frame: pd.DataFrame) -> pd.DataFrame:
    """Compare means, medians, effect sizes, and permutation evidence."""
    groups = frame.groupby("broke_down")[FEATURES]
    means, medians, variances = groups.mean(), groups.median(), groups.var()
    counts = groups.size()
    pooled_sd = np.sqrt(
        ((counts[0] - 1) * variances.loc[0] + (counts[1] - 1) * variances.loc[1])
        / (counts.sum() - 2)
    )
    difference = means.loc[1] - means.loc[0]
    effect = difference.div(pooled_sd.replace(0, np.nan)).fillna(0)
    # Shuffle outcomes to measure how often random groups have as large a mean gap.
    values = frame[FEATURES].to_numpy()
    labels = frame["broke_down"].to_numpy()
    rng = np.random.default_rng(SEED)
    hits = np.zeros(len(FEATURES))
    for _ in range(PERMUTATIONS):
        shuffled = rng.permutation(labels)
        gap = values[shuffled == 1].mean(axis=0) - values[shuffled == 0].mean(axis=0)
        hits += np.abs(gap) >= np.abs(difference.to_numpy())
    p_values = (hits + 1) / (PERMUTATIONS + 1)
    # Holm adjustment accounts for testing five candidate columns at once.
    order = np.argsort(p_values)
    adjusted = np.empty(len(FEATURES))
    adjusted[order] = np.minimum(
        1, np.maximum.accumulate(p_values[order] * np.arange(len(FEATURES), 0, -1))
    )
    comparison = pd.DataFrame({
        "mean_no_breakdown": means.loc[0], "mean_breakdown": means.loc[1],
        "median_no_breakdown": medians.loc[0], "median_breakdown": medians.loc[1],
        "effect_size": effect, "p_adjusted": adjusted,
    })
    comparison["separates"] = (
        comparison["effect_size"].abs().ge(MIN_EFFECT)
        & comparison["p_adjusted"].le(MAX_P)
    )
    return comparison


def rank_cars(frame: pd.DataFrame, comparison: pd.DataFrame) -> pd.DataFrame:
    """Weight normalized readings by effect size, without using individual outcomes."""
    selected = comparison.index[comparison["use_in_score"]].tolist()
    if not selected:
        raise ValueError("No robust separating factors found; cannot justify a risk score.")
    effects = comparison.loc[selected, "effect_size"]
    weights = effects.abs() / effects.abs().sum()
    ranked = frame.copy()
    ranked["reading_inconsistent"] = frame["km_since_service"] > frame["odometer_km"]
    ranked["risk_score"] = 0.0
    for column in selected:
        low, high = frame[column].min(), frame[column].max()
        if high == low:
            raise ValueError(f"Selected factor {column} is constant.")
        normalized = (frame[column] - low) / (high - low)
        if effects[column] < 0:
            normalized = 1 - normalized
        ranked[f"points_{column}"] = 100 * weights[column] * normalized
        ranked["risk_score"] += ranked[f"points_{column}"]
    ranked["risk_score"] = ranked["risk_score"].clip(0, 100)
    # Sort unrounded scores; ID gives deterministic ordering for exact ties.
    ranked = ranked.sort_values(["risk_score", "car_id"], ascending=[False, True])
    ranked.insert(0, "rank", range(1, len(ranked) + 1))
    return ranked


def main() -> None:
    """Print the analysis and top ten, and save all comparisons and rankings."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path(__file__).with_name("fleet_history.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "analysis_outputs")
    args = parser.parse_args()
    frame = load_history(args.input)
    print(f"Step 1: {len(frame)} cars; outcomes: {frame['broke_down'].value_counts().to_dict()}")
    print("car_id identifies cars; broke_down is the outcome. Neither is a scoring factor.")
    inconsistent = frame["km_since_service"] > frame["odometer_km"]
    print(f"Data warning: {int(inconsistent.sum())} cars have service distance above total mileage:")
    print(", ".join(frame.loc[inconsistent, "car_id"]) or "None")
    comparison = compare_groups(frame)
    sensitivity = compare_groups(frame.loc[~inconsistent]) if inconsistent.any() else comparison.copy()
    comparison["clean_effect_size"] = sensitivity["effect_size"]
    comparison["clean_p_adjusted"] = sensitivity["p_adjusted"]
    comparison["use_in_score"] = comparison["separates"] & sensitivity["separates"]
    print("Selection: |effect size| >= 0.5 and Holm-adjusted permutation p <= 0.05,")
    print("both in the full data and after excluding inconsistent records.")
    print(comparison.to_string(float_format=lambda value: f"{value:.4f}"))
    print("These are associations in this sample, not proof of causation or future accuracy.")
    print("No supported separation here does not prove that a factor can never matter.")
    print("Step 2: Score only robust factors; normalize each to 0..1 over this fleet.")
    effects = comparison.loc[comparison["use_in_score"], "effect_size"]
    weights = effects.abs() / effects.abs().sum()
    for column, weight in weights.items():
        print(f"  {column}: weight {weight:.4%}; {'higher' if effects[column] > 0 else 'lower'} is riskier")
    print("risk_score = 100 * weighted average of normalized readings.")
    print("Relative priority from 0 to 100, not a calibrated breakdown probability.")
    ranked = rank_cars(frame, comparison)
    print("Step 3: Top 10 cars, highest risk first (historical outcome shown only for reference).")
    print(ranked.head(10).to_string(index=False, float_format=lambda value: f"{value:.2f}"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(args.output_dir / "factor_comparison.csv", index_label="factor")
    sensitivity.to_csv(args.output_dir / "sensitivity_comparison.csv", index_label="factor")
    ranked.to_csv(args.output_dir / "fleet_risk_ranking.csv", index=False)
    print(f"Saved full {len(ranked)}-car ranking and comparisons to {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
