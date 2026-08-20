"""Thread-safe in-process API telemetry for low-cardinality service metrics.

Cloud Run already emits platform request/resource metrics. This module adds a small
application-level view for model-serving telemetry and an internal metrics endpoint.
It intentionally avoids user-level labels to prevent high-cardinality metrics.
"""

from __future__ import annotations

import math
import threading
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class TelemetryStore:
    """Collect bounded latency/prediction samples and counters in memory."""

    max_samples: int = 5000
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _request_count: int = 0
    _status_counts: Counter[int] = field(default_factory=Counter, init=False, repr=False)
    _endpoint_counts: Counter[str] = field(default_factory=Counter, init=False, repr=False)
    _latencies_ms: deque[float] = field(init=False, repr=False)
    _prediction_values: defaultdict[str, deque[float]] = field(
        default_factory=lambda: defaultdict(deque), init=False, repr=False
    )
    _errors: int = 0

    def __post_init__(self) -> None:
        self._latencies_ms = deque(maxlen=self.max_samples)

    def record_request(self, endpoint: str, status_code: int, latency_ms: float) -> None:
        """Record a completed request without retaining request payloads."""
        with self._lock:
            self._request_count += 1
            self._status_counts[int(status_code)] += 1
            self._endpoint_counts[str(endpoint)] += 1
            if math.isfinite(latency_ms):
                self._latencies_ms.append(float(latency_ms))
            if int(status_code) >= 500:
                self._errors += 1

    def record_prediction(self, kind: str, **values: float | None) -> None:
        """Record bounded numeric prediction-distribution samples."""
        with self._lock:
            for name, value in values.items():
                if value is None:
                    continue
                numeric = float(value)
                if not math.isfinite(numeric):
                    continue
                key = f"{kind}.{name}"
                bucket = self._prediction_values[key]
                if bucket.maxlen != self.max_samples:
                    bucket = deque(bucket, maxlen=self.max_samples)
                    self._prediction_values[key] = bucket
                bucket.append(numeric)

    @staticmethod
    def _summary(values: list[float]) -> dict[str, float | int | None]:
        if not values:
            return {"count": 0, "mean": None, "p50": None, "p95": None, "p99": None}
        arr = np.asarray(values, dtype=float)
        return {
            "count": int(arr.size),
            "mean": float(arr.mean()),
            "p50": float(np.quantile(arr, 0.50)),
            "p95": float(np.quantile(arr, 0.95)),
            "p99": float(np.quantile(arr, 0.99)),
        }

    def snapshot(self) -> dict[str, Any]:
        """Return low-cardinality aggregate telemetry suitable for an internal endpoint."""
        with self._lock:
            request_count = self._request_count
            error_rate = self._errors / request_count if request_count else 0.0
            prediction_summary = {
                key: self._summary(list(values)) for key, values in sorted(self._prediction_values.items())
            }
            return {
                "request_count": request_count,
                "error_rate": float(error_rate),
                "http_status_counts": {str(k): v for k, v in sorted(self._status_counts.items())},
                "endpoint_counts": dict(sorted(self._endpoint_counts.items())),
                "latency_ms": self._summary(list(self._latencies_ms)),
                "predictions": prediction_summary,
            }
