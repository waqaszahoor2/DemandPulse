"""Doubly robust AIPW estimation."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def estimate_aipw(
    outcome: Sequence[float],
    treatment: Sequence[int],
    propensity: Sequence[float],
    mu1: Sequence[float],
    mu0: Sequence[float],
    *,
    epsilon: float = 1e-6,
) -> dict[str, float]:
    """Estimate ATE with the augmented inverse-probability weighted score."""
    y = np.asarray(outcome, dtype=float)
    t = np.asarray(treatment, dtype=float)
    p = np.asarray(propensity, dtype=float)
    m1 = np.asarray(mu1, dtype=float)
    m0 = np.asarray(mu0, dtype=float)
    lengths = {len(y), len(t), len(p), len(m1), len(m0)}
    if len(lengths) != 1:
        raise ValueError("AIPW inputs must have equal lengths")
    mask = np.isfinite(y) & np.isfinite(t) & np.isfinite(p) & np.isfinite(m1) & np.isfinite(m0)
    y, t, p, m1, m0 = y[mask], t[mask], p[mask], m1[mask], m0[mask]
    if len(y) == 0:
        raise ValueError("No valid AIPW observations")
    if not set(np.unique(t)).issubset({0.0, 1.0}):
        raise ValueError("Treatment must be binary")
    p = np.clip(p, epsilon, 1.0 - epsilon)
    score = m1 - m0 + t * (y - m1) / p - (1.0 - t) * (y - m0) / (1.0 - p)
    ate = float(score.mean())
    se = float(score.std(ddof=1) / np.sqrt(len(score))) if len(score) > 1 else np.nan
    return {
        "ate": ate,
        "standard_error": se,
        "ci_lower": ate - 1.96 * se if np.isfinite(se) else np.nan,
        "ci_upper": ate + 1.96 * se if np.isfinite(se) else np.nan,
        "observations": float(len(score)),
    }
