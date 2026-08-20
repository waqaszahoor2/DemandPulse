"""MLflow Model Registry helpers and champion/candidate promotion checks."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from demandpulse.config import DEFAULT_CONFIG, DemandPulseConfig
from demandpulse.mlops.tracking import _import_mlflow, configure_mlflow


def register_model(
    model_uri: str,
    model_name: str,
    *,
    tags: Mapping[str, str] | None = None,
    await_registration_for: int = 300,
    config: DemandPulseConfig = DEFAULT_CONFIG,
) -> Any:
    """Register an already-logged MLflow model without promoting it."""
    if not model_uri or not model_name:
        raise ValueError("model_uri and model_name are required")
    configure_mlflow(config=config)
    mlflow = _import_mlflow()
    version = mlflow.register_model(
        model_uri=model_uri,
        name=model_name,
        await_registration_for=await_registration_for,
    )
    if tags:
        client = mlflow.tracking.MlflowClient()
        for key, value in tags.items():
            client.set_model_version_tag(model_name, str(version.version), str(key), str(value))
    return version


def get_model_version(
    model_name: str,
    *,
    alias: str | None = None,
    version: str | int | None = None,
    config: DemandPulseConfig = DEFAULT_CONFIG,
) -> Any:
    """Resolve a model version by explicit version or registry alias."""
    if bool(alias) == bool(version is not None):
        raise ValueError("Specify exactly one of alias or version")
    configure_mlflow(config=config)
    mlflow = _import_mlflow()
    client = mlflow.tracking.MlflowClient()
    if alias:
        return client.get_model_version_by_alias(model_name, alias)
    return client.get_model_version(model_name, str(version))


def load_registered_model(
    model_name: str,
    *,
    alias: str | None = "champion",
    version: str | int | None = None,
    config: DemandPulseConfig = DEFAULT_CONFIG,
) -> Any:
    """Load a registered model via MLflow pyfunc."""
    if alias and version is not None:
        raise ValueError("Use alias or version, not both")
    configure_mlflow(config=config)
    mlflow = _import_mlflow()
    if version is not None:
        uri = f"models:/{model_name}/{version}"
    elif alias:
        uri = f"models:/{model_name}@{alias}"
    else:
        raise ValueError("alias or version is required")
    return mlflow.pyfunc.load_model(uri)


def set_model_alias(
    model_name: str,
    alias: str,
    version: str | int,
    *,
    config: DemandPulseConfig = DEFAULT_CONFIG,
) -> None:
    """Assign a registry alias such as champion or candidate."""
    if not alias.strip():
        raise ValueError("alias cannot be empty")
    configure_mlflow(config=config)
    mlflow = _import_mlflow()
    client = mlflow.tracking.MlflowClient()
    client.set_registered_model_alias(model_name, alias, str(version))


def candidate_passes_champion_rules(
    candidate_metrics: Mapping[str, float],
    champion_metrics: Mapping[str, float],
    *,
    required_tests_passed: bool,
    max_abs_bias: float | None = None,
    max_coverage_drop: float | None = None,
) -> tuple[bool, list[str]]:
    """Evaluate configurable model-promotion gates without changing registry aliases.

    WAPE improvement is mandatory when both models expose WAPE. Bias/calibration gates
    are only applied when the caller/configuration supplies explicit thresholds.
    """
    reasons: list[str] = []
    if not required_tests_passed:
        reasons.append("required tests did not pass")
    if "WAPE" not in candidate_metrics or "WAPE" not in champion_metrics:
        reasons.append("WAPE is required for champion comparison")
    elif float(candidate_metrics["WAPE"]) >= float(champion_metrics["WAPE"]):
        reasons.append("candidate WAPE did not improve")

    if max_abs_bias is not None:
        bias = candidate_metrics.get("Bias")
        if bias is None or abs(float(bias)) > max_abs_bias:
            reasons.append("candidate bias exceeds configured limit")

    if max_coverage_drop is not None and "Coverage" in champion_metrics:
        coverage = candidate_metrics.get("Coverage")
        if coverage is None:
            reasons.append("candidate coverage is missing")
        elif float(coverage) < float(champion_metrics["Coverage"]) - max_coverage_drop:
            reasons.append("candidate calibration regressed beyond configured limit")

    return not reasons, reasons


def promote_candidate(
    model_name: str,
    candidate_version: str | int,
    *,
    candidate_metrics: Mapping[str, float],
    champion_metrics: Mapping[str, float],
    required_tests_passed: bool,
    max_abs_bias: float | None = None,
    max_coverage_drop: float | None = None,
    apply: bool = False,
    config: DemandPulseConfig = DEFAULT_CONFIG,
) -> tuple[bool, list[str]]:
    """Evaluate a candidate and optionally promote it while retaining a rollback alias.

    `apply=False` is the default safety mode. Promotion changes registry aliases only
    when all configured gates pass and the caller explicitly opts in.
    """
    passed, reasons = candidate_passes_champion_rules(
        candidate_metrics,
        champion_metrics,
        required_tests_passed=required_tests_passed,
        max_abs_bias=max_abs_bias,
        max_coverage_drop=max_coverage_drop,
    )
    if not passed or not apply:
        return passed, reasons

    current = get_model_version(model_name, alias="champion", config=config)
    previous_version = str(getattr(current, "version"))
    set_model_alias(model_name, "previous_champion", previous_version, config=config)
    set_model_alias(model_name, "champion", candidate_version, config=config)
    return True, []


def rollback_champion(
    model_name: str,
    *,
    rollback_alias: str = "previous_champion",
    config: DemandPulseConfig = DEFAULT_CONFIG,
) -> str:
    """Move `champion` back to a pre-recorded rollback alias and return its version."""
    previous = get_model_version(model_name, alias=rollback_alias, config=config)
    version = str(getattr(previous, "version"))
    set_model_alias(model_name, "champion", version, config=config)
    return version
