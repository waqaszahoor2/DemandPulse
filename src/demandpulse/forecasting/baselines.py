"""Leakage-safe temporal forecasting baselines."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from demandpulse.config import SERIES_KEYS


def _sorted(
    frame: pd.DataFrame,
    group_cols: Sequence[str],
    date_col: str,
    target_col: str,
) -> pd.DataFrame:
    required = set(group_cols) | {date_col, target_col}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise KeyError(f"Missing baseline columns: {missing}")
    return frame.sort_values([*group_cols, date_col])


def naive_forecast(
    frame: pd.DataFrame,
    *,
    target_col: str = "sale_amount",
    group_cols: Sequence[str] = SERIES_KEYS,
    date_col: str = "dt",
) -> pd.Series:
    """Forecast each series with its previous observed demand."""
    ordered = _sorted(frame, group_cols, date_col, target_col)
    prediction = ordered.groupby(list(group_cols), sort=False, observed=True)[target_col].shift(1)
    return prediction.reindex(frame.index)


def seasonal_naive_forecast(
    frame: pd.DataFrame,
    *,
    season_length: int = 7,
    target_col: str = "sale_amount",
    group_cols: Sequence[str] = SERIES_KEYS,
    date_col: str = "dt",
) -> pd.Series:
    """Forecast each series with demand from one seasonal lag ago."""
    if season_length <= 0:
        raise ValueError("season_length must be positive")
    ordered = _sorted(frame, group_cols, date_col, target_col)
    prediction = ordered.groupby(list(group_cols), sort=False, observed=True)[target_col].shift(season_length)
    return prediction.reindex(frame.index)


def moving_average_forecast(
    frame: pd.DataFrame,
    *,
    window: int = 7,
    target_col: str = "sale_amount",
    group_cols: Sequence[str] = SERIES_KEYS,
    date_col: str = "dt",
) -> pd.Series:
    """Forecast from the mean of the previous ``window`` observations only."""
    if window <= 0:
        raise ValueError("window must be positive")
    ordered = _sorted(frame, group_cols, date_col, target_col)
    prediction = ordered.groupby(list(group_cols), sort=False, observed=True)[target_col].transform(
        lambda s: s.shift(1).rolling(window, min_periods=window).mean()
    )
    return prediction.reindex(frame.index)
