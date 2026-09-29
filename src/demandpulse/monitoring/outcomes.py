"""Actual-outcome validation and immutable prediction/outcome matching utilities."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

PREDICTION_JOIN_KEYS = ["store_id", "product_id", "forecast_date"]
ACTUAL_COLUMNS = ["store_id", "product_id", "date", "actual_sales"]


def validate_actual_outcomes(actuals: pd.DataFrame) -> pd.DataFrame:
    """Validate actual sales without modifying prediction-time records."""
    missing = sorted(set(ACTUAL_COLUMNS) - set(actuals.columns))
    if missing:
        raise ValueError(f"Actual-outcome data missing required columns: {missing}")
    frame = actuals.loc[:, ACTUAL_COLUMNS].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame["actual_sales"] = pd.to_numeric(frame["actual_sales"], errors="raise")
    if frame["actual_sales"].isna().any() or not np.isfinite(frame["actual_sales"]).all():
        raise ValueError("actual_sales must be finite and non-missing")
    if (frame["actual_sales"] < 0).any():
        raise ValueError("actual_sales cannot be negative")
    duplicates = frame.duplicated(["store_id", "product_id", "date"], keep=False)
    if duplicates.any():
        raise ValueError("Actual-outcome data contains duplicate store/product/date keys")
    return frame


def join_predictions_with_actuals(
    predictions: pd.DataFrame,
    actuals: pd.DataFrame,
    *,
    required_prediction_columns: Sequence[str] = (
        "store_id",
        "product_id",
        "forecast_date",
        "p50",
        "model_version",
    ),
) -> pd.DataFrame:
    """Join immutable prediction records to later-arriving actuals on business keys."""
    missing = sorted(set(required_prediction_columns) - set(predictions.columns))
    if missing:
        raise ValueError(f"Prediction log missing required columns: {missing}")
    pred = predictions.copy()
    pred["forecast_date"] = pd.to_datetime(pred["forecast_date"], errors="raise")
    actual = validate_actual_outcomes(actuals).rename(columns={"date": "forecast_date"})
    merged = pred.merge(actual, on=PREDICTION_JOIN_KEYS, how="inner", validate="many_to_one")
    return merged
