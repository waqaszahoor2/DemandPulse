"""Leakage-safe historical demand and stockout features."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from demandpulse.config import SERIES_KEYS


def add_lag_features(
    frame: pd.DataFrame,
    *,
    group_cols: Sequence[str] = SERIES_KEYS,
    date_col: str = "dt",
    target_col: str = "sale_amount",
    stockout_col: str = "stock_hour6_22_cnt",
    lags: Sequence[int] = (1, 2, 3, 7, 14, 28),
    rolling_windows: Sequence[int] = (7, 14, 28),
) -> pd.DataFrame:
    """Create historical features using only observations before the current row.

    Every target-based rolling statistic explicitly applies ``shift(1)`` before
    rolling, preventing the current target from entering its own predictors.
    """
    required = set(group_cols) | {date_col, target_col}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise KeyError(f"Missing lag-feature columns: {missing}")
    if any(lag <= 0 for lag in lags):
        raise ValueError("lags must be positive")
    if any(window <= 0 for window in rolling_windows):
        raise ValueError("rolling windows must be positive")

    out = frame.copy().sort_values([*group_cols, date_col]).reset_index(drop=True)
    grouped = out.groupby(list(group_cols), sort=False, observed=True)

    for lag in lags:
        out[f"lag_{lag}"] = grouped[target_col].shift(lag)

    for window in rolling_windows:
        shifted = grouped[target_col].transform(lambda s: s.shift(1))
        grouped_shifted = shifted.groupby([out[col] for col in group_cols], sort=False)
        out[f"rolling_mean_{window}"] = grouped_shifted.transform(
            lambda s, w=window: s.rolling(w, min_periods=w).mean()
        )
        out[f"rolling_std_{window}"] = grouped_shifted.transform(
            lambda s, w=window: s.rolling(w, min_periods=w).std()
        )

    shifted = grouped[target_col].transform(lambda s: s.shift(1))
    grouped_shifted = shifted.groupby([out[col] for col in group_cols], sort=False)
    out["rolling_min_7"] = grouped_shifted.transform(lambda s: s.rolling(7, min_periods=7).min())
    out["rolling_max_7"] = grouped_shifted.transform(lambda s: s.rolling(7, min_periods=7).max())

    if stockout_col in out:
        out["stockout_flag"] = out[stockout_col].gt(0).astype("int8")
        stock_group = out.groupby(list(group_cols), sort=False, observed=True)["stockout_flag"]
        out["stockout_lag_1"] = stock_group.shift(1)
        out["stockout_lag_7"] = stock_group.shift(7)
    return out


def drop_incomplete_history(
    frame: pd.DataFrame,
    required_feature_columns: Sequence[str],
) -> pd.DataFrame:
    """Remove rows lacking the historical context required by selected features."""
    missing = sorted(set(required_feature_columns) - set(frame.columns))
    if missing:
        raise KeyError(f"Missing required historical features: {missing}")
    return frame.dropna(subset=list(required_feature_columns)).copy()
