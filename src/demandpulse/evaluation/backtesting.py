"""Chronological rolling-origin evaluation utilities."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RollingFold:
    fold: int
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    validation_start: pd.Timestamp
    validation_end: pd.Timestamp


def create_rolling_folds(
    dates: Sequence[Any],
    *,
    forecast_horizon: int = 7,
    n_folds: int = 3,
) -> list[RollingFold]:
    """Create end-anchored chronological folds with non-overlapping validation windows."""
    if forecast_horizon <= 0 or n_folds <= 0:
        raise ValueError("forecast_horizon and n_folds must be positive")
    unique_dates = pd.DatetimeIndex(pd.to_datetime(pd.Series(dates), errors="raise").dropna().unique()).sort_values()
    minimum = n_folds * forecast_horizon + 1
    if len(unique_dates) < minimum:
        raise ValueError(
            f"Need at least {minimum} unique dates for {n_folds} folds of horizon {forecast_horizon}; "
            f"got {len(unique_dates)}"
        )

    folds: list[RollingFold] = []
    for fold_index in range(n_folds):
        validation_start_idx = len(unique_dates) - (n_folds - fold_index) * forecast_horizon
        validation_end_idx = validation_start_idx + forecast_horizon - 1
        train_end_idx = validation_start_idx - 1
        fold = RollingFold(
            fold=fold_index + 1,
            train_start=pd.Timestamp(unique_dates[0]),
            train_end=pd.Timestamp(unique_dates[train_end_idx]),
            validation_start=pd.Timestamp(unique_dates[validation_start_idx]),
            validation_end=pd.Timestamp(unique_dates[validation_end_idx]),
        )
        if not fold.train_end < fold.validation_start:
            raise AssertionError("Temporal leakage in generated fold")
        folds.append(fold)
    return folds


def run_backtest(
    frame: pd.DataFrame,
    folds: Sequence[RollingFold],
    fit_predict: Callable[[pd.DataFrame, pd.DataFrame, RollingFold], Sequence[float]],
    *,
    date_col: str = "dt",
    target_col: str = "sale_amount",
) -> pd.DataFrame:
    """Run a user-supplied fit/predict routine on strictly chronological folds."""
    if date_col not in frame or target_col not in frame:
        raise KeyError(f"Frame must contain {date_col!r} and {target_col!r}")
    out_rows: list[dict[str, Any]] = []
    for fold in folds:
        train = frame.loc[frame[date_col] <= fold.train_end].copy()
        valid = frame.loc[frame[date_col].between(fold.validation_start, fold.validation_end)].copy()
        if train.empty or valid.empty:
            raise ValueError(f"Fold {fold.fold} has empty train or validation data")
        if not train[date_col].max() < valid[date_col].min():
            raise AssertionError(f"Fold {fold.fold} violates chronology")
        prediction = np.asarray(fit_predict(train, valid, fold), dtype=float)
        if len(prediction) != len(valid):
            raise ValueError(f"Fold {fold.fold} prediction length mismatch")
        for index, actual, pred in zip(valid.index, valid[target_col].to_numpy(dtype=float), prediction):
            out_rows.append({"fold": fold.fold, "row_index": index, "actual": actual, "prediction": pred})
    return pd.DataFrame(out_rows)
