"""Configurable alert evaluation for API, ML, and drift signals."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class AlertThresholds:
    """Operational thresholds; override per environment rather than treating as universal."""

    error_rate_yellow: float = 0.02
    error_rate_red: float = 0.05
    latency_p95_yellow_ms: float = 500.0
    latency_p95_red_ms: float = 1500.0
    psi_yellow: float = 0.10
    psi_red: float = 0.25
    wape_degradation_yellow: float = 0.10
    wape_degradation_red: float = 0.25
    absolute_bias_yellow: float = 0.10
    absolute_bias_red: float = 0.20
    coverage_deviation_yellow: float = 0.08
    coverage_deviation_red: float = 0.15


def _level(value: float, yellow: float, red: float) -> str:
    if not math.isfinite(value):
        return "YELLOW"
    if value >= red:
        return "RED"
    if value >= yellow:
        return "YELLOW"
    return "GREEN"


def evaluate_alerts(
    signals: Mapping[str, float | bool],
    *,
    thresholds: AlertThresholds = AlertThresholds(),
) -> dict[str, str]:
    """Evaluate meaningful alert conditions without alerting on every small fluctuation."""
    result: dict[str, str] = {}
    if bool(signals.get("service_unavailable", False)):
        result["service_availability"] = "RED"
    if bool(signals.get("model_load_failure", False)):
        result["model_loading"] = "RED"
    if "error_rate" in signals:
        result["api_error_rate"] = _level(
            float(signals["error_rate"]), thresholds.error_rate_yellow, thresholds.error_rate_red
        )
    if "latency_p95_ms" in signals:
        result["api_latency"] = _level(
            float(signals["latency_p95_ms"]), thresholds.latency_p95_yellow_ms, thresholds.latency_p95_red_ms
        )
    if "max_psi" in signals:
        result["feature_drift"] = _level(float(signals["max_psi"]), thresholds.psi_yellow, thresholds.psi_red)
    if "wape_relative_degradation" in signals:
        result["forecast_degradation"] = _level(
            max(float(signals["wape_relative_degradation"]), 0.0),
            thresholds.wape_degradation_yellow,
            thresholds.wape_degradation_red,
        )
    if "absolute_bias" in signals:
        result["forecast_bias"] = _level(
            abs(float(signals["absolute_bias"])),
            thresholds.absolute_bias_yellow,
            thresholds.absolute_bias_red,
        )
    if "coverage_deviation" in signals:
        result["interval_calibration"] = _level(
            abs(float(signals["coverage_deviation"])),
            thresholds.coverage_deviation_yellow,
            thresholds.coverage_deviation_red,
        )
    return result
