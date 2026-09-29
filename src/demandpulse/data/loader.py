"""Remote Hugging Face data access with streaming materialization."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

import numpy as np
import pandas as pd

from demandpulse.config import DEFAULT_CONFIG, DemandPulseConfig
from demandpulse.data.sampling import series_selected
from demandpulse.data.validation import DataValidationError, validate_schema
from demandpulse.utils.logging import get_logger

logger = get_logger(__name__)


def load_remote_dataset(
    split: str,
    config: DemandPulseConfig = DEFAULT_CONFIG,
) -> Any:
    """Load a FreshRetailNet-50K split as a Hugging Face IterableDataset."""
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise RuntimeError(
            "The 'datasets' package is required. Install the project dependencies first."
        ) from exc

    try:
        stream = load_dataset(config.dataset_id, split=split, streaming=True)
    except Exception as exc:
        raise RuntimeError(f"Unable to stream split={split!r} from {config.dataset_id!r}: {exc}") from exc

    feature_names = list(getattr(getattr(stream, "features", None), "keys", lambda: [])())
    if not feature_names and getattr(stream, "features", None) is not None:
        feature_names = list(stream.features)
    if feature_names:
        validate_schema(
            feature_names,
            config.required_columns,
            allowed_columns=config.required_columns,
            allow_extra=False,
        )
    return stream


def _batch_iterator(stream: Any, batch_size: int) -> Iterable[dict[str, Sequence[Any]]]:
    if hasattr(stream, "iter"):
        yield from stream.iter(batch_size=batch_size)
        return
    if hasattr(stream, "batch"):
        yield from stream.batch(batch_size=batch_size)
        return
    raise TypeError("Expected a Hugging Face IterableDataset supporting iter(batch_size=...) or batch(...).")


def materialize_stream(
    stream: Any,
    *,
    sample_percent: float = 30.0,
    batch_size: int = 50_000,
    columns: Sequence[str] | None = None,
    max_rows: int | None = None,
) -> pd.DataFrame:
    """Materialize a deterministic subset of complete store-product series.

    Rows are processed in batches, filtered by the stable series hash, accumulated
    as DataFrames, and concatenated once. ``max_rows`` is intended for development
    smoke runs; production experiments should leave it unset so selected series
    are not truncated by a row cap.
    """
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    if max_rows is not None and max_rows <= 0:
        raise ValueError("max_rows must be positive when provided")

    selected_columns = list(columns or DEFAULT_CONFIG.materialized_columns)
    frames: list[pd.DataFrame] = []
    selection_cache: dict[tuple[Any, Any], bool] = {}
    rows_processed = 0
    rows_selected = 0

    for batch_number, batch in enumerate(_batch_iterator(stream, batch_size), start=1):
        batch_df = pd.DataFrame(batch)
        rows_processed += len(batch_df)
        validate_schema(batch_df.columns, ("store_id", "product_id"), allow_extra=True)
        missing_materialized = sorted(set(selected_columns) - set(batch_df.columns))
        if missing_materialized:
            raise DataValidationError(
                f"Streaming batch is missing materialized columns: {missing_materialized}"
            )

        keep = np.fromiter(
            (
                series_selected(store_id, product_id, sample_percent, selection_cache)
                for store_id, product_id in zip(batch_df["store_id"], batch_df["product_id"])
            ),
            dtype=bool,
            count=len(batch_df),
        )
        if keep.any():
            selected = batch_df.loc[keep, selected_columns].copy()
            if max_rows is not None:
                remaining = max_rows - rows_selected
                selected = selected.iloc[:remaining]
            frames.append(selected)
            rows_selected += len(selected)

        if batch_number % 20 == 0:
            logger.info(
                "stream materialization progress: processed=%s selected=%s",
                f"{rows_processed:,}",
                f"{rows_selected:,}",
            )
        if max_rows is not None and rows_selected >= max_rows:
            logger.warning(
                "Development max_rows=%s reached; complete-series preservation beyond the cap is not guaranteed.",
                max_rows,
            )
            break

    if not frames:
        raise RuntimeError(
            "No rows were selected. Check the sample percentage and remote dataset availability."
        )

    result = pd.concat(frames, ignore_index=True, copy=False)
    result.attrs["rows_processed"] = rows_processed
    result.attrs["rows_selected"] = rows_selected
    result.attrs["series_sample_percent"] = sample_percent
    logger.info(
        "materialization complete: processed=%s selected=%s",
        f"{rows_processed:,}",
        f"{rows_selected:,}",
    )
    return result


def _load_split(
    split: str,
    config: DemandPulseConfig,
    sample_percent: float | None,
    max_rows: int | None,
) -> pd.DataFrame:
    stream = load_remote_dataset(split, config)
    frame = materialize_stream(
        stream,
        sample_percent=config.series_sample_percent if sample_percent is None else sample_percent,
        batch_size=config.stream_batch_size,
        columns=config.materialized_columns,
        max_rows=max_rows,
    )
    try:
        frame["dt"] = pd.to_datetime(frame["dt"], errors="raise")
    except Exception as exc:
        raise DataValidationError(f"Failed to parse dt in {split}: {exc}") from exc
    return frame


def load_train_data(
    config: DemandPulseConfig = DEFAULT_CONFIG,
    *,
    sample_percent: float | None = None,
    max_rows: int | None = None,
) -> pd.DataFrame:
    """Stream and materialize the configured training split."""
    return _load_split("train", config, sample_percent, max_rows)


def load_eval_data(
    config: DemandPulseConfig = DEFAULT_CONFIG,
    *,
    sample_percent: float | None = None,
    max_rows: int | None = None,
) -> pd.DataFrame:
    """Stream and materialize the official evaluation split."""
    return _load_split("eval", config, sample_percent, max_rows)
