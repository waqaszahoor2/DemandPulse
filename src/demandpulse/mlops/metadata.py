"""Safe model metadata structures shared by MLflow and the API."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ModelMetadata:
    """Serializable, non-secret metadata for a trained DemandPulse model."""

    model_name: str
    model_version: str
    model_type: str
    dataset_id: str
    sample_percentage: float
    forecast_horizon: int | None = None
    features: tuple[str, ...] = field(default_factory=tuple)
    metrics: Mapping[str, float] = field(default_factory=dict)
    training_timestamp: str | None = None
    git_commit: str | None = None
    status: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe public metadata."""
        payload = asdict(self)
        payload["features"] = list(self.features)
        payload["metrics"] = {str(k): float(v) for k, v in self.metrics.items()}
        return payload

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> ModelMetadata:
        """Build metadata from a persisted mapping while ignoring unknown fields."""
        metrics = values.get("metrics") or {}
        return cls(
            model_name=str(values.get("model_name", "unknown")),
            model_version=str(values.get("model_version", "unknown")),
            model_type=str(values.get("model_type", "unknown")),
            dataset_id=str(values.get("dataset_id", "unknown")),
            sample_percentage=float(values.get("sample_percentage", 0.0)),
            forecast_horizon=(
                int(values["forecast_horizon"]) if values.get("forecast_horizon") is not None else None
            ),
            features=tuple(str(v) for v in values.get("features", ())),
            metrics={str(k): float(v) for k, v in metrics.items()},
            training_timestamp=(
                str(values["training_timestamp"]) if values.get("training_timestamp") is not None else None
            ),
            git_commit=str(values["git_commit"]) if values.get("git_commit") else None,
            status=str(values.get("status", "unknown")),
        )


def utc_now_iso() -> str:
    """Return a timezone-aware UTC timestamp for model/run metadata."""
    return datetime.now(timezone.utc).isoformat()


def feature_list_tag(features: Sequence[str]) -> str:
    """Compact deterministic representation suitable for MLflow tags."""
    return ",".join(str(value) for value in features)
