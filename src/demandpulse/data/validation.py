"""Strict data-quality checks for DemandPulse inputs."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np
import pandas as pd


class DataValidationError(ValueError):
    """Raised when data violates a non-repairable production contract."""


def validate_schema(
    actual_columns: Iterable[str],
    required_columns: Sequence[str],
    *,
    allowed_columns: Sequence[str] | None = None,
    allow_extra: bool = False,
) -> None:
    """Validate required fields and optionally reject unexpected schema changes."""
    actual = set(actual_columns)
    required = set(required_columns)
    missing = sorted(required - actual)
    if missing:
        raise DataValidationError(f"Missing required columns: {missing}")

    allowed = set(allowed_columns if allowed_columns is not None else required_columns)
    unexpected = sorted(actual - allowed)
    if unexpected and not allow_extra:
        raise DataValidationError(f"Unexpected schema columns: {unexpected}")


def validate_duplicate_keys(
    frame: pd.DataFrame,
    keys: Sequence[str] = ("store_id", "product_id", "dt"),
) -> None:
    """Raise with representative duplicate rows instead of silently deduplicating."""
    validate_schema(frame.columns, keys, allow_extra=True)
    mask = frame.duplicated(list(keys), keep=False)
    if mask.any():
        examples = frame.loc[mask, list(keys)].head(10).to_dict(orient="records")
        raise DataValidationError(
            f"Duplicate key rows detected for {list(keys)}; examples={examples}"
        )


def validate_dates(frame: pd.DataFrame, date_col: str = "dt") -> None:
    """Require a parseable, non-missing datetime column."""
    if date_col not in frame:
        raise DataValidationError(f"Missing date column: {date_col}")
    if not pd.api.types.is_datetime64_any_dtype(frame[date_col]):
        try:
            parsed = pd.to_datetime(frame[date_col], errors="raise")
        except Exception as exc:
            raise DataValidationError(f"Invalid dates in {date_col}: {exc}") from exc
        if parsed.isna().any():
            raise DataValidationError(f"Missing dates found in {date_col}")
    elif frame[date_col].isna().any():
        raise DataValidationError(f"Missing dates found in {date_col}")


def validate_target(frame: pd.DataFrame, target_col: str = "sale_amount") -> None:
    """Require a present, numeric, non-negative demand target."""
    if target_col not in frame:
        raise DataValidationError(f"Missing target column: {target_col}")
    target = frame[target_col]
    if target.isna().any():
        raise DataValidationError(f"Missing values found in target {target_col}")
    if not pd.api.types.is_numeric_dtype(target):
        raise DataValidationError(f"Target {target_col} must be numeric, got {target.dtype}")
    invalid = ~np.isfinite(target.to_numpy(dtype=float))
    if invalid.any():
        raise DataValidationError(f"Non-finite values found in target {target_col}")
    if (target < 0).any():
        raise DataValidationError(f"Negative demand found in target {target_col}")


def validate_dtypes(frame: pd.DataFrame, date_col: str = "dt", target_col: str = "sale_amount") -> None:
    """Validate critical production dtypes."""
    validate_dates(frame, date_col)
    if target_col in frame and not pd.api.types.is_numeric_dtype(frame[target_col]):
        raise DataValidationError(f"{target_col} must be numeric")


def validate_frame(
    frame: pd.DataFrame,
    *,
    required_columns: Sequence[str],
    allowed_columns: Sequence[str] | None = None,
    key_columns: Sequence[str] = ("store_id", "product_id", "dt"),
    target_col: str = "sale_amount",
) -> None:
    """Run the main strict data contract for a materialized split."""
    validate_schema(
        frame.columns,
        required_columns,
        allowed_columns=allowed_columns or required_columns,
        allow_extra=allowed_columns is None,
    )
    validate_dates(frame)
    validate_target(frame, target_col)
    validate_duplicate_keys(frame, key_columns)
    validate_dtypes(frame, target_col=target_col)


def validate_train_eval_chronology(
    train: pd.DataFrame,
    evaluation: pd.DataFrame,
    date_col: str = "dt",
) -> None:
    """Require a strictly future official evaluation period."""
    validate_dates(train, date_col)
    validate_dates(evaluation, date_col)
    train_max = pd.Timestamp(train[date_col].max())
    eval_min = pd.Timestamp(evaluation[date_col].min())
    if not train_max < eval_min:
        raise DataValidationError(
            "Official evaluation is not strictly later than training: "
            f"max(train)={train_max}, min(eval)={eval_min}"
        )
