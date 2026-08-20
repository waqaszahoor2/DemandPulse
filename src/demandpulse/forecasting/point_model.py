"""Global LightGBM point forecasting model lifecycle."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

from demandpulse.config import DEFAULT_CONFIG, DemandPulseConfig

FORBIDDEN_SAME_DAY_PREDICTORS = {
    "sale_amount",
    "hours_sale",
    "hours_stock_status",
    "stock_hour6_22_cnt",
}


def infer_category_levels(
    frame: pd.DataFrame,
    categorical_features: Sequence[str],
) -> dict[str, list[Any]]:
    """Capture training-only category vocabularies for safe future alignment."""
    levels: dict[str, list[Any]] = {}
    for column in categorical_features:
        if column not in frame:
            raise KeyError(f"Missing categorical feature: {column}")
        values = pd.Series(frame[column].dropna().unique()).tolist()
        levels[column] = values
    return levels


def align_categorical_features(
    frame: pd.DataFrame,
    category_levels: Mapping[str, Sequence[Any]],
) -> pd.DataFrame:
    """Align categories; unseen future values become missing rather than crashing."""
    out = frame.copy()
    for column, levels in category_levels.items():
        if column not in out:
            raise KeyError(f"Missing categorical feature at prediction time: {column}")
        out[column] = pd.Categorical(out[column], categories=list(levels))
    return out


def _validate_feature_columns(feature_columns: Sequence[str]) -> None:
    forbidden = sorted(set(feature_columns) & FORBIDDEN_SAME_DAY_PREDICTORS)
    if forbidden:
        raise ValueError(
            "Same-day leakage-prone predictors are forbidden in the point model: "
            f"{forbidden}"
        )


def train_point_model(
    train_frame: pd.DataFrame,
    *,
    target_col: str = "sale_amount",
    feature_columns: Sequence[str] | None = None,
    categorical_features: Sequence[str] | None = None,
    validation_frame: pd.DataFrame | None = None,
    params: Mapping[str, Any] | None = None,
    config: DemandPulseConfig = DEFAULT_CONFIG,
) -> tuple[LGBMRegressor, dict[str, Any]]:
    """Train one global LightGBM point model with reproducible categorical handling."""
    features = list(feature_columns or config.point_features)
    categorical = [c for c in (categorical_features or config.categorical_features) if c in features]
    _validate_feature_columns(features)
    missing = sorted((set(features) | {target_col}) - set(train_frame.columns))
    if missing:
        raise KeyError(f"Training frame is missing columns: {missing}")

    levels = infer_category_levels(train_frame, categorical)
    aligned_train = align_categorical_features(train_frame[features], levels)
    y_train = train_frame[target_col].to_numpy(dtype=float)

    model_params = dict(config.point_lgbm_params)
    if params:
        model_params.update(params)
    model_params["random_state"] = config.random_state
    model = LGBMRegressor(**model_params)

    fit_kwargs: dict[str, Any] = {"categorical_feature": categorical}
    if validation_frame is not None:
        valid_missing = sorted((set(features) | {target_col}) - set(validation_frame.columns))
        if valid_missing:
            raise KeyError(f"Validation frame is missing columns: {valid_missing}")
        aligned_valid = align_categorical_features(validation_frame[features], levels)
        fit_kwargs["eval_set"] = [(aligned_valid, validation_frame[target_col].to_numpy(dtype=float))]
        fit_kwargs["callbacks"] = [lgb.early_stopping(50, verbose=False)]

    model.fit(aligned_train, y_train, **fit_kwargs)
    metadata = {
        "feature_columns": features,
        "categorical_features": categorical,
        "category_levels": levels,
        "target_col": target_col,
        "random_state": config.random_state,
        "best_iteration": int(model.best_iteration_ or model.n_estimators),
    }
    return model, metadata


def predict_point(
    model: Any,
    frame: pd.DataFrame,
    metadata: Mapping[str, Any],
    *,
    clip_nonnegative: bool = True,
) -> np.ndarray:
    """Predict demand with training-consistent categories and optional non-negative clipping."""
    features = list(metadata["feature_columns"])
    missing = sorted(set(features) - set(frame.columns))
    if missing:
        raise KeyError(f"Prediction frame is missing features: {missing}")
    X = align_categorical_features(frame[features], metadata.get("category_levels", {}))
    prediction = np.asarray(model.predict(X), dtype=float)
    if clip_nonnegative:
        prediction = np.maximum(prediction, 0.0)
    return prediction


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def save_point_model(
    model: LGBMRegressor,
    path: str | Path,
    metadata: Mapping[str, Any],
) -> tuple[Path, Path]:
    """Save the native LightGBM booster plus JSON metadata sidecar."""
    model_path = Path(path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    if not hasattr(model, "booster_"):
        raise ValueError("Model must be a fitted LGBMRegressor")
    model.booster_.save_model(str(model_path))
    metadata_path = model_path.with_suffix(model_path.suffix + ".metadata.json")
    metadata_path.write_text(json.dumps(_json_safe(dict(metadata)), indent=2), encoding="utf-8")
    return model_path, metadata_path


def load_point_model(path: str | Path) -> tuple[lgb.Booster, dict[str, Any]]:
    """Load a native LightGBM booster and its metadata sidecar."""
    model_path = Path(path)
    metadata_path = model_path.with_suffix(model_path.suffix + ".metadata.json")
    if not model_path.exists():
        raise FileNotFoundError(model_path)
    if not metadata_path.exists():
        raise FileNotFoundError(metadata_path)
    booster = lgb.Booster(model_file=str(model_path))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    return booster, metadata
