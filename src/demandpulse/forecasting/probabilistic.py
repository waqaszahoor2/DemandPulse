"""Quantile LightGBM forecasting and conformal calibration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

from demandpulse.config import DEFAULT_CONFIG, DemandPulseConfig
from demandpulse.forecasting.point_model import (
    FORBIDDEN_SAME_DAY_PREDICTORS,
    align_categorical_features,
    infer_category_levels,
)


def train_quantile_model(
    train_frame: pd.DataFrame,
    quantile: float,
    *,
    target_col: str = "target",
    feature_columns: Sequence[str],
    categorical_features: Sequence[str] = (),
    params: Mapping[str, Any] | None = None,
    config: DemandPulseConfig = DEFAULT_CONFIG,
) -> tuple[LGBMRegressor, dict[str, Any]]:
    """Train one conditional quantile model for one direct forecast horizon."""
    if not 0.0 < quantile < 1.0:
        raise ValueError("quantile must lie strictly between 0 and 1")
    leakage = sorted(set(feature_columns) & FORBIDDEN_SAME_DAY_PREDICTORS)
    if leakage:
        raise ValueError(f"Leakage-prone same-day features are forbidden: {leakage}")
    missing = sorted((set(feature_columns) | {target_col}) - set(train_frame.columns))
    if missing:
        raise KeyError(f"Quantile training frame is missing: {missing}")

    categorical = [c for c in categorical_features if c in feature_columns]
    levels = infer_category_levels(train_frame, categorical)
    X = align_categorical_features(train_frame[list(feature_columns)], levels)
    y = train_frame[target_col].to_numpy(dtype=float)

    model_params = dict(config.quantile_lgbm_params)
    if params:
        model_params.update(params)
    model_params["random_state"] = config.random_state
    model = LGBMRegressor(objective="quantile", alpha=quantile, **model_params)
    model.fit(X, y, categorical_feature=categorical)
    metadata = {
        "quantile": quantile,
        "feature_columns": list(feature_columns),
        "categorical_features": categorical,
        "category_levels": levels,
        "target_col": target_col,
    }
    return model, metadata


def train_quantile_models(
    horizon_frames: Mapping[int, pd.DataFrame],
    *,
    feature_columns: Sequence[str],
    categorical_features: Sequence[str] = (),
    quantiles: Sequence[float] = (0.10, 0.50, 0.90),
    target_col: str = "target",
    params: Mapping[str, Any] | None = None,
    config: DemandPulseConfig = DEFAULT_CONFIG,
) -> dict[int, dict[float, tuple[LGBMRegressor, dict[str, Any]]]]:
    """Train direct horizon-specific quantile models sequentially."""
    result: dict[int, dict[float, tuple[LGBMRegressor, dict[str, Any]]]] = {}
    for horizon in sorted(horizon_frames):
        if horizon < 1 or horizon > config.forecast_horizon:
            raise ValueError(f"Unsupported horizon {horizon}")
        result[horizon] = {}
        for quantile in quantiles:
            result[horizon][float(quantile)] = train_quantile_model(
                horizon_frames[horizon],
                float(quantile),
                target_col=target_col,
                feature_columns=feature_columns,
                categorical_features=categorical_features,
                params=params,
                config=config,
            )
    return result


def predict_quantiles(
    models: Mapping[float, tuple[Any, Mapping[str, Any]]],
    frame: pd.DataFrame,
    *,
    clip_nonnegative: bool = False,
) -> pd.DataFrame:
    """Generate raw quantiles. Crossing repair remains an explicit separate step."""
    out = pd.DataFrame(index=frame.index)
    for quantile, (model, metadata) in sorted(models.items()):
        features = list(metadata["feature_columns"])
        X = align_categorical_features(frame[features], metadata.get("category_levels", {}))
        pred = np.asarray(model.predict(X), dtype=float)
        if clip_nonnegative:
            pred = np.maximum(pred, 0.0)
        out[f"p{int(round(quantile * 100)):02d}"] = pred
    return out


def repair_quantile_crossing(
    predictions: pd.DataFrame,
    columns: Sequence[str] = ("p10", "p50", "p90"),
) -> pd.DataFrame:
    """Repair crossing by monotonic row-wise sorting after diagnostics are recorded."""
    missing = sorted(set(columns) - set(predictions.columns))
    if missing:
        raise KeyError(f"Missing quantile columns: {missing}")
    out = predictions.copy()
    out[list(columns)] = np.sort(out[list(columns)].to_numpy(dtype=float), axis=1)
    return out


def calculate_conformal_adjustment(
    actual: Sequence[float],
    lower: Sequence[float],
    upper: Sequence[float],
    *,
    alpha: float = 0.20,
) -> float:
    """Compute the finite-sample CQR adjustment with a higher empirical quantile."""
    y = np.asarray(actual, dtype=float)
    lo = np.asarray(lower, dtype=float)
    hi = np.asarray(upper, dtype=float)
    if not (len(y) == len(lo) == len(hi)):
        raise ValueError("actual/lower/upper lengths differ")
    mask = np.isfinite(y) & np.isfinite(lo) & np.isfinite(hi)
    y, lo, hi = y[mask], lo[mask], hi[mask]
    if len(y) == 0:
        raise ValueError("No valid calibration observations")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in (0, 1)")
    scores = np.maximum(lo - y, y - hi)
    level = min(1.0, np.ceil((len(scores) + 1) * (1 - alpha)) / len(scores))
    try:
        return float(np.quantile(scores, level, method="higher"))
    except TypeError:
        return float(np.quantile(scores, level, interpolation="higher"))


def apply_conformal_adjustment(
    lower: Sequence[float],
    upper: Sequence[float],
    q_hat: float,
    *,
    clip_lower_at_zero: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    """Expand a quantile interval by the train-calibration CQR adjustment."""
    if q_hat < 0 or not np.isfinite(q_hat):
        raise ValueError("q_hat must be finite and non-negative")
    lo = np.asarray(lower, dtype=float) - q_hat
    hi = np.asarray(upper, dtype=float) + q_hat
    if clip_lower_at_zero:
        lo = np.maximum(lo, 0.0)
    return lo, hi
