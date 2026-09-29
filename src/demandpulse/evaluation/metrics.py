"""Point, probabilistic, and causal diagnostic metrics."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


from typing import Any


def _paired_arrays(y_true: Any, y_pred: Any) -> tuple[np.ndarray, np.ndarray]:
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(y_pred, dtype=float)
    if y.shape != p.shape:
        raise ValueError(f"Input shapes differ: {y.shape} vs {p.shape}")
    mask = np.isfinite(y) & np.isfinite(p)
    return y[mask], p[mask]


def mae(y_true: Any, y_pred: Any) -> float:
    y, p = _paired_arrays(y_true, y_pred)
    return float(np.mean(np.abs(y - p))) if len(y) else np.nan


def rmse(y_true: Any, y_pred: Any) -> float:
    y, p = _paired_arrays(y_true, y_pred)
    return float(np.sqrt(np.mean((y - p) ** 2))) if len(y) else np.nan


def wape(y_true: Any, y_pred: Any) -> float:
    """Weighted absolute percentage error; returns NaN for a zero target denominator."""
    y, p = _paired_arrays(y_true, y_pred)
    denominator = np.abs(y).sum()
    return float(np.abs(y - p).sum() / denominator) if denominator > 0 else np.nan


def bias(y_true: Any, y_pred: Any) -> float:
    """Positive values indicate aggregate over-forecasting; negative values under-forecasting."""
    y, p = _paired_arrays(y_true, y_pred)
    denominator = np.abs(y).sum()
    return float((p - y).sum() / denominator) if denominator > 0 else np.nan


def point_metrics(y_true: Any, y_pred: Any) -> dict[str, float]:
    y, p = _paired_arrays(y_true, y_pred)
    return {
        "mae": mae(y, p),
        "rmse": rmse(y, p),
        "wape": wape(y, p),
        "bias": bias(y, p),
        "observations": float(len(y)),
    }


def pinball_loss(y_true: Sequence[float], y_pred: Sequence[float], quantile: float) -> float:
    if not 0.0 < quantile < 1.0:
        raise ValueError("quantile must be in (0, 1)")
    y, p = _paired_arrays(y_true, y_pred)
    if not len(y):
        return np.nan
    residual = y - p
    loss = np.where(residual >= 0, quantile * residual, (quantile - 1.0) * residual)
    return float(np.mean(loss))


def interval_coverage(y_true: Sequence[float], lower: Sequence[float], upper: Sequence[float]) -> float:
    y = np.asarray(y_true, dtype=float)
    lo = np.asarray(lower, dtype=float)
    hi = np.asarray(upper, dtype=float)
    if not (y.shape == lo.shape == hi.shape):
        raise ValueError("Interval input shapes differ")
    mask = np.isfinite(y) & np.isfinite(lo) & np.isfinite(hi)
    if not mask.any():
        return np.nan
    if np.any(lo[mask] > hi[mask]):
        raise ValueError("Lower interval bound exceeds upper bound")
    return float(np.mean((lo[mask] <= y[mask]) & (y[mask] <= hi[mask])))


def interval_width(lower: Sequence[float], upper: Sequence[float]) -> float:
    lo = np.asarray(lower, dtype=float)
    hi = np.asarray(upper, dtype=float)
    if lo.shape != hi.shape:
        raise ValueError("Interval bound shapes differ")
    mask = np.isfinite(lo) & np.isfinite(hi)
    if not mask.any():
        return np.nan
    if np.any(lo[mask] > hi[mask]):
        raise ValueError("Lower interval bound exceeds upper bound")
    return float(np.mean(hi[mask] - lo[mask]))


def interval_score(
    y_true: Sequence[float],
    lower: Sequence[float],
    upper: Sequence[float],
    *,
    alpha: float = 0.20,
) -> float:
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in (0, 1)")
    y = np.asarray(y_true, dtype=float)
    lo = np.asarray(lower, dtype=float)
    hi = np.asarray(upper, dtype=float)
    if not (y.shape == lo.shape == hi.shape):
        raise ValueError("Interval input shapes differ")
    mask = np.isfinite(y) & np.isfinite(lo) & np.isfinite(hi)
    y, lo, hi = y[mask], lo[mask], hi[mask]
    if not len(y):
        return np.nan
    if np.any(lo > hi):
        raise ValueError("Lower interval bound exceeds upper bound")
    score = hi - lo
    score += (2.0 / alpha) * (lo - y) * (y < lo)
    score += (2.0 / alpha) * (y - hi) * (y > hi)
    return float(np.mean(score))


def standardized_mean_difference(
    treated: Sequence[float],
    control: Sequence[float],
    *,
    treated_weights: Sequence[float] | None = None,
    control_weights: Sequence[float] | None = None,
) -> float:
    """Standardized mean difference using pooled group variances."""

    def prepare(values: Sequence[float], weights: Sequence[float] | None):
        x = np.asarray(values, dtype=float)
        mask = np.isfinite(x)
        if weights is None:
            return x[mask], None
        w = np.asarray(weights, dtype=float)
        if len(w) != len(x):
            raise ValueError("Weights and values must have equal lengths")
        mask &= np.isfinite(w)
        return x[mask], w[mask]

    x1, w1 = prepare(treated, treated_weights)
    x0, w0 = prepare(control, control_weights)
    if len(x1) == 0 or len(x0) == 0:
        return np.nan

    def weighted_stats(x: np.ndarray, weights: np.ndarray | None) -> tuple[float, float]:
        if weights is None:
            return float(x.mean()), float(x.var(ddof=1)) if len(x) > 1 else 0.0
        if np.any(weights < 0) or weights.sum() <= 0:
            raise ValueError("Weights must be non-negative with positive sum")
        mean = float(np.average(x, weights=weights))
        variance = float(np.average((x - mean) ** 2, weights=weights))
        return mean, variance

    mean1, var1 = weighted_stats(x1, w1)
    mean0, var0 = weighted_stats(x0, w0)
    pooled = np.sqrt((var1 + var0) / 2.0)
    if pooled == 0:
        return 0.0 if np.isclose(mean1, mean0) else np.inf
    return float((mean1 - mean0) / pooled)
