"""Batch production monitoring helpers joining forecasts, actuals, and drift signals."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from demandpulse.evaluation.metrics import bias, interval_coverage, interval_width, mae, pinball_loss, wape
from demandpulse.monitoring.drift import category_drift, ks_statistic, population_stability_index
from demandpulse.monitoring.outcomes import join_predictions_with_actuals


def forecast_performance_by_group(
    predictions: pd.DataFrame,
    actuals: pd.DataFrame,
    *,
    group_columns: Sequence[str] = ("model_version", "horizon"),
) -> pd.DataFrame:
    """Calculate point/probabilistic metrics after actual outcomes arrive."""
    merged = join_predictions_with_actuals(predictions, actuals)
    missing_groups = sorted(set(group_columns) - set(merged.columns))
    if missing_groups:
        raise ValueError(f"Monitoring join missing grouping columns: {missing_groups}")
    rows: list[dict[str, object]] = []
    for key, group in merged.groupby(list(group_columns), dropna=False, observed=True):
        keys = key if isinstance(key, tuple) else (key,)
        row: dict[str, object] = dict(zip(group_columns, keys))
        actual = group["actual_sales"].to_numpy(dtype=float)
        p50 = group["p50"].to_numpy(dtype=float)
        row.update({
            "observations": len(group),
            "MAE": mae(actual, p50),
            "WAPE": wape(actual, p50),
            "Bias": bias(actual, p50),
            "P50_Pinball": pinball_loss(actual, p50, 0.50),
        })
        if {"p10", "p90"}.issubset(group.columns) and group[["p10", "p90"]].notna().all(axis=None):
            p10 = group["p10"].to_numpy(dtype=float)
            p90 = group["p90"].to_numpy(dtype=float)
            row.update({
                "P10_Pinball": pinball_loss(actual, p10, 0.10),
                "P90_Pinball": pinball_loss(actual, p90, 0.90),
                "Coverage": interval_coverage(actual, p10, p90),
                "Interval_Width": interval_width(p10, p90),
            })
        rows.append(row)
    return pd.DataFrame(rows)


def drift_report(
    reference: pd.DataFrame,
    recent: pd.DataFrame,
    *,
    numeric_features: Sequence[str],
    categorical_features: Sequence[str],
) -> pd.DataFrame:
    """Create one drift table using PSI/KS and categorical total variation."""
    rows: list[dict[str, object]] = []
    for feature in numeric_features:
        if feature not in reference or feature not in recent:
            continue
        ks = ks_statistic(reference[feature], recent[feature])
        rows.append({
            "feature": feature,
            "kind": "numeric",
            "psi": population_stability_index(reference[feature], recent[feature]),
            "ks_statistic": ks["statistic"],
            "ks_pvalue": ks["pvalue"],
            "new_category_rate": np.nan,
            "total_variation": np.nan,
        })
    for feature in categorical_features:
        if feature not in reference or feature not in recent:
            continue
        cat = category_drift(reference[feature], recent[feature])
        rows.append({
            "feature": feature,
            "kind": "categorical",
            "psi": population_stability_index(reference[feature], recent[feature]),
            "ks_statistic": np.nan,
            "ks_pvalue": np.nan,
            **cat,
        })
    return pd.DataFrame(rows)


def target_drift_summary(reference_target, recent_target) -> dict[str, float]:
    """Compare observed-demand level, variance, zero rate and simple intermittency."""
    ref = pd.to_numeric(pd.Series(reference_target), errors="coerce").dropna().to_numpy(dtype=float)
    cur = pd.to_numeric(pd.Series(recent_target), errors="coerce").dropna().to_numpy(dtype=float)
    if len(ref) == 0 or len(cur) == 0:
        raise ValueError("reference and recent targets must each contain observations")
    if (ref < 0).any() or (cur < 0).any():
        raise ValueError("demand targets cannot be negative")
    ref_zero = float(np.mean(ref == 0))
    cur_zero = float(np.mean(cur == 0))
    return {
        "reference_mean": float(np.mean(ref)),
        "recent_mean": float(np.mean(cur)),
        "mean_change": float(np.mean(cur) - np.mean(ref)),
        "reference_variance": float(np.var(ref)),
        "recent_variance": float(np.var(cur)),
        "variance_change": float(np.var(cur) - np.var(ref)),
        "reference_zero_sales_rate": ref_zero,
        "recent_zero_sales_rate": cur_zero,
        "zero_sales_rate_change": cur_zero - ref_zero,
        "reference_intermittency": ref_zero,
        "recent_intermittency": cur_zero,
        "intermittency_change": cur_zero - ref_zero,
    }
