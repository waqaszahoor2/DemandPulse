"""Potential-outcome treatment-effect summaries."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd


def estimate_ate(mu1: Sequence[float], mu0: Sequence[float]) -> float:
    """Estimate the average potential-outcome contrast E[mu1(X)-mu0(X)]."""
    treated = np.asarray(mu1, dtype=float)
    control = np.asarray(mu0, dtype=float)
    if len(treated) != len(control):
        raise ValueError("mu1 and mu0 lengths differ")
    diff = treated - control
    diff = diff[np.isfinite(diff)]
    return float(diff.mean()) if len(diff) else np.nan


def estimate_att(
    outcome: Sequence[float],
    treatment: Sequence[int],
    mu0: Sequence[float],
) -> float:
    """Estimate ATT as observed treated outcome minus estimated untreated potential outcome."""
    y = np.asarray(outcome, dtype=float)
    t = np.asarray(treatment, dtype=int)
    m0 = np.asarray(mu0, dtype=float)
    if not (len(y) == len(t) == len(m0)):
        raise ValueError("ATT inputs have unequal lengths")
    mask = (t == 1) & np.isfinite(y) & np.isfinite(m0)
    return float(np.mean(y[mask] - m0[mask])) if mask.any() else np.nan


def estimate_cate(
    treated_model: Any,
    control_model: Any,
    features: pd.DataFrame,
) -> np.ndarray:
    """Estimate conditional treatment effects with a T-learner contrast."""
    mu1 = np.asarray(treated_model.predict(features), dtype=float)
    mu0 = np.asarray(control_model.predict(features), dtype=float)
    if len(mu1) != len(mu0):
        raise ValueError("T-learner potential-outcome prediction lengths differ")
    return mu1 - mu0
