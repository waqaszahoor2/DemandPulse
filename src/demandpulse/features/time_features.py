"""Calendar features known at forecast time."""

from __future__ import annotations

import pandas as pd


def add_time_features(frame: pd.DataFrame, date_col: str = "dt") -> pd.DataFrame:
    """Add deterministic calendar features without using the target."""
    if date_col not in frame:
        raise KeyError(f"Missing date column: {date_col}")
    out = frame.copy()
    if not pd.api.types.is_datetime64_any_dtype(out[date_col]):
        out[date_col] = pd.to_datetime(out[date_col], errors="raise")
    out["day_of_week"] = out[date_col].dt.dayofweek.astype("int8")
    out["day_of_month"] = out[date_col].dt.day.astype("int8")
    out["week_of_year"] = out[date_col].dt.isocalendar().week.astype("int16")
    out["month"] = out[date_col].dt.month.astype("int8")
    out["is_weekend"] = out["day_of_week"].isin([5, 6]).astype("int8")
    if "holiday_flag" in out:
        out["is_holiday"] = out["holiday_flag"].fillna(0).astype("int8")
    return out
