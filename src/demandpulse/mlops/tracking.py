"""MLflow experiment tracking helpers with local-safe defaults."""

from __future__ import annotations

import json
import math
import numbers
import subprocess
from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from demandpulse.config import DEFAULT_CONFIG, DemandPulseConfig
from demandpulse.utils.logging import get_logger

logger = get_logger(__name__)

DEFAULT_EXPERIMENTS = {
    "point": "demandpulse-point-forecasting",
    "probabilistic": "demandpulse-probabilistic",
    "causal": "demandpulse-causal",
}


def _import_mlflow() -> Any:
    try:
        import mlflow  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "MLflow is not installed. Install the DemandPulse API/MLOps dependencies first."
        ) from exc
    return mlflow


def get_git_commit(project_root: str | Path | None = None) -> str | None:
    """Return the current Git commit when the project is inside a Git repository."""
    cwd = Path(project_root).resolve() if project_root else None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = result.stdout.strip()
    return value or None


def configure_mlflow(
    tracking_uri: str | None = None,
    *,
    config: DemandPulseConfig = DEFAULT_CONFIG,
) -> str:
    """Configure MLflow and return the active tracking URI.

    Local default uses a file-based MLflow store so development/tests do not require
    a remote tracking server.
    """
    mlflow = _import_mlflow()
    uri = tracking_uri or config.mlflow_tracking_uri
    mlflow.set_tracking_uri(uri)
    return str(mlflow.get_tracking_uri())


def get_or_create_experiment(name: str) -> str:
    """Return an MLflow experiment ID, creating the experiment when necessary."""
    if not name.strip():
        raise ValueError("experiment name cannot be empty")
    mlflow = _import_mlflow()
    existing = mlflow.get_experiment_by_name(name)
    if existing is not None:
        return str(existing.experiment_id)
    return str(mlflow.create_experiment(name))


def _log_params_safe(mlflow: Any, params: Mapping[str, Any]) -> None:
    serializable: dict[str, Any] = {}
    for key, value in params.items():
        if isinstance(value, (dict, list, tuple, set)):
            serializable[str(key)] = json.dumps(value, sort_keys=True, default=str)
        else:
            serializable[str(key)] = value
    if serializable:
        mlflow.log_params(serializable)


def _log_metrics_safe(mlflow: Any, metrics: Mapping[str, float]) -> None:
    valid = {
        str(key): float(value)
        for key, value in metrics.items()
        if value is not None and isinstance(value, numbers.Real) and math.isfinite(float(value))
    }
    if valid:
        mlflow.log_metrics(valid)


@contextmanager
def tracking_run(
    *,
    experiment_name: str,
    run_name: str,
    params: Mapping[str, Any] | None = None,
    metrics: Mapping[str, float] | None = None,
    artifacts: Sequence[str | Path] = (),
    tags: Mapping[str, str] | None = None,
    config: DemandPulseConfig = DEFAULT_CONFIG,
) -> Iterator[Any]:
    """Start an MLflow run and log supplied executed results/artifacts.

    No metrics are computed or fabricated here; callers must provide metrics produced
    by their actual evaluation pipeline.
    """
    configure_mlflow(config=config)
    mlflow = _import_mlflow()
    experiment_id = get_or_create_experiment(experiment_name)
    run_tags = dict(tags or {})
    git_commit = get_git_commit(config.project_root)
    if git_commit:
        run_tags.setdefault("git_commit", git_commit)
    run_tags.setdefault("dataset_id", config.dataset_id)
    run_tags.setdefault("sample_percentage", str(config.series_sample_percent))

    with mlflow.start_run(
        experiment_id=experiment_id,
        run_name=run_name,
        tags=run_tags or None,
    ) as run:
        base_params = {
            "dataset_id": config.dataset_id,
            "series_sample_percent": config.series_sample_percent,
            "random_state": config.random_state,
        }
        base_params.update(params or {})
        _log_params_safe(mlflow, base_params)
        _log_metrics_safe(mlflow, metrics or {})
        for artifact in artifacts:
            path = Path(artifact)
            if not path.exists():
                raise FileNotFoundError(f"MLflow artifact does not exist: {path}")
            if path.is_dir():
                mlflow.log_artifacts(str(path))
            else:
                mlflow.log_artifact(str(path))
        yield run


def log_experiment_run(
    *,
    experiment_name: str,
    run_name: str,
    params: Mapping[str, Any] | None = None,
    metrics: Mapping[str, float] | None = None,
    artifacts: Sequence[str | Path] = (),
    tags: Mapping[str, str] | None = None,
    config: DemandPulseConfig = DEFAULT_CONFIG,
) -> str:
    """Log a complete run and return its MLflow run ID."""
    with tracking_run(
        experiment_name=experiment_name,
        run_name=run_name,
        params=params,
        metrics=metrics,
        artifacts=artifacts,
        tags=tags,
        config=config,
    ) as run:
        return str(run.info.run_id)
