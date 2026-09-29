"""Propensity modeling and inverse-probability weights."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

POST_TREATMENT_OR_OUTCOME_COLUMNS = {
    "activity_flag",
    "sale_amount",
    "discount",
    "discount_pct",
    "hours_sale",
    "hours_stock_status",
    "stock_hour6_22_cnt",
}


def train_propensity_model(
    frame: pd.DataFrame,
    *,
    treatment_col: str = "activity_flag",
    feature_columns: Sequence[str],
    categorical_features: Sequence[str] = (),
    random_state: int = 42,
    max_iter: int = 500,
) -> Pipeline:
    """Fit P(T=1|X) using pre-treatment covariates only."""
    forbidden = sorted(set(feature_columns) & POST_TREATMENT_OR_OUTCOME_COLUMNS)
    if forbidden:
        raise ValueError(f"Post-treatment/outcome columns are forbidden in propensity X: {forbidden}")
    missing = sorted((set(feature_columns) | {treatment_col}) - set(frame.columns))
    if missing:
        raise KeyError(f"Propensity frame is missing: {missing}")
    treatment = frame[treatment_col].to_numpy()
    unique = set(np.unique(treatment))
    if not unique.issubset({0, 1}) or len(unique) < 2:
        raise ValueError("Treatment must be binary and contain both treated and control observations")

    categorical = [c for c in categorical_features if c in feature_columns]
    numeric = [c for c in feature_columns if c not in categorical]
    numeric_pipe = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    category_pipe = Pipeline(
        [
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=True)),
        ]
    )
    preprocess = ColumnTransformer(
        [("numeric", numeric_pipe, numeric), ("categorical", category_pipe, categorical)],
        remainder="drop",
    )
    model = LogisticRegression(
        max_iter=max_iter,
        random_state=random_state,
        solver="lbfgs",
    )
    pipeline = Pipeline([("preprocess", preprocess), ("model", model)])
    pipeline.fit(frame[list(feature_columns)], treatment)
    return pipeline


def predict_propensity(
    model: Any,
    frame: pd.DataFrame,
    feature_columns: Sequence[str],
    *,
    epsilon: float = 1e-6,
) -> np.ndarray:
    """Predict propensity scores and protect downstream denominators."""
    if not 0 < epsilon < 0.5:
        raise ValueError("epsilon must be in (0, 0.5)")
    p = np.asarray(model.predict_proba(frame[list(feature_columns)])[:, 1], dtype=float)
    return np.clip(p, epsilon, 1.0 - epsilon)


def calculate_ipw_weights(
    treatment: Sequence[int],
    propensity: Sequence[float],
    *,
    estimand: str = "ate",
    stabilized: bool = False,
    clip_quantiles: tuple[float, float] | None = None,
) -> np.ndarray:
    """Calculate ATE or ATT inverse-probability weights."""
    t = np.asarray(treatment, dtype=float)
    p = np.asarray(propensity, dtype=float)
    if len(t) != len(p):
        raise ValueError("treatment and propensity lengths differ")
    if not set(np.unique(t)).issubset({0.0, 1.0}):
        raise ValueError("treatment must be binary")
    if np.any((p <= 0) | (p >= 1) | ~np.isfinite(p)):
        raise ValueError("propensity scores must be finite and strictly between 0 and 1")

    estimand = estimand.lower()
    if estimand == "ate":
        weights = t / p + (1.0 - t) / (1.0 - p)
        if stabilized:
            pt = t.mean()
            weights = t * pt / p + (1.0 - t) * (1.0 - pt) / (1.0 - p)
    elif estimand == "att":
        weights = t + (1.0 - t) * p / (1.0 - p)
    else:
        raise ValueError("estimand must be 'ate' or 'att'")

    if clip_quantiles is not None:
        lo_q, hi_q = clip_quantiles
        if not 0 <= lo_q < hi_q <= 1:
            raise ValueError("clip_quantiles must satisfy 0 <= low < high <= 1")
        lo, hi = np.quantile(weights, [lo_q, hi_q])
        weights = np.clip(weights, lo, hi)
    return weights
