"""Privacy-conscious prediction event logging and optional local Parquet export."""

from __future__ import annotations

import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd

from demandpulse.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class PredictionLogRecord:
    """Minimal immutable prediction record used for later outcome matching."""

    prediction_id: str
    request_id: str
    timestamp: str
    store_id: str
    product_id: str
    forecast_date: str
    horizon: int
    p10: float | None
    p50: float
    p90: float | None
    model_version: str

    @classmethod
    def create(
        cls,
        *,
        request_id: str,
        store_id: Any,
        product_id: Any,
        forecast_date: Any,
        horizon: int,
        p50: float,
        model_version: str,
        p10: float | None = None,
        p90: float | None = None,
    ) -> PredictionLogRecord:
        return cls(
            prediction_id=str(uuid4()),
            request_id=str(request_id),
            timestamp=datetime.now(timezone.utc).isoformat(),
            store_id=str(store_id),
            product_id=str(product_id),
            forecast_date=str(forecast_date),
            horizon=int(horizon),
            p10=None if p10 is None else float(p10),
            p50=float(p50),
            p90=None if p90 is None else float(p90),
            model_version=str(model_version),
        )


class PredictionLogger:
    """Emit structured prediction events and optionally retain a bounded local buffer.

    In Cloud Run, stdout is captured by Cloud Logging. Production persistence should
    route these structured events through a Cloud Logging sink to BigQuery or Cloud
    Storage. Local Parquet export is available for development/batch validation only.
    """

    def __init__(self, *, local_parquet_path: str | Path | None = None, max_buffer: int = 10000) -> None:
        self.local_parquet_path = Path(local_parquet_path) if local_parquet_path else None
        self.max_buffer = int(max_buffer)
        self._records: list[dict[str, Any]] = []
        self._lock = threading.RLock()

    def log(self, record: PredictionLogRecord) -> None:
        payload = asdict(record)
        logger.info("prediction_event", extra={"event_type": "prediction", **payload})
        if self.local_parquet_path is None:
            return
        with self._lock:
            self._records.append(payload)
            if len(self._records) >= self.max_buffer:
                self.flush()

    def flush(self) -> None:
        """Append buffered records to a local Parquet dataset file."""
        if self.local_parquet_path is None:
            return
        with self._lock:
            if not self._records:
                return
            self.local_parquet_path.parent.mkdir(parents=True, exist_ok=True)
            new = pd.DataFrame(self._records)
            if self.local_parquet_path.exists():
                existing = pd.read_parquet(self.local_parquet_path)
                new = pd.concat([existing, new], ignore_index=True)
            new.to_parquet(self.local_parquet_path, index=False)
            self._records.clear()
