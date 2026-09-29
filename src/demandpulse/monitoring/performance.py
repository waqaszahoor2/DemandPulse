"""Forecast-performance and calibration monitoring status."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np

from demandpulse.evaluation.metrics import (
    bias,
    interval_coverage,
    interval_width,
    pinball_loss,
    wape,
)

STATUS_ORDER = {"GREEN": 0, "YELLOW": 1, "RED": 2}


@dataclass(frozen=True)
class MonitoringThresholds:
    """Configurable degradation thresholds; values are project policy, not universal constants."""

    wape_relative_yellow: float = 0.10
    wape_relative_red: float = 0.25
    absolute_bias_yellow: float = 0.10
    absolute_bias_red: float = 0.20
    coverage_deviation_yellow: float = 0.08
    coverage_deviation_red: float = 0.15
    width_ratio_yellow: float = 1.25
    width_ratio_red: float = 1.75


def _status(value: float, yellow: float, red: float) -> str:
    if not np.isfinite(value):
        return "YELLOW"
    if value >= red:
        return "RED"
    if value >= yellow:
        return "YELLOW"
    return "GREEN"


def calculate_performance_snapshot(
    actual,
    p50,
    *,
    p10=None,
    p90=None,
    nominal_coverage: float = 0.80,
) -> dict[str, float]:
    """Calculate point and optional probabilistic monitoring metrics."""
    result = {
        "wape": wape(actual, p50),
        "bias": bias(actual, p50),
        "p50_pinball": pinball_loss(actual, p50, 0.50),
    }
    if p10 is not None and p90 is not None:
        result.update(
            {
                "p10_pinball": pinball_loss(actual, p10, 0.10),
                "p90_pinball": pinball_loss(actual, p90, 0.90),
                "coverage": interval_coverage(actual, p10, p90),
                "interval_width": interval_width(p10, p90),
                "coverage_deviation": abs(interval_coverage(actual, p10, p90) - nominal_coverage),
            }
        )
    return result


def monitoring_status(
    current: Mapping[str, float],
    reference: Mapping[str, float],
    *,
    thresholds: MonitoringThresholds = MonitoringThresholds(),
) -> dict[str, str | float]:
    """Create GREEN/YELLOW/RED status from degradation and calibration signals."""
    ref_wape = float(reference.get("wape", np.nan))
    cur_wape = float(current.get("wape", np.nan))
    wape_degradation = (
        (cur_wape - ref_wape) / abs(ref_wape)
        if np.isfinite(cur_wape) and np.isfinite(ref_wape) and ref_wape != 0
        else np.nan
    )
    statuses = {
        "wape_status": _status(
            max(wape_degradation, 0.0) if np.isfinite(wape_degradation) else np.nan,
            thresholds.wape_relative_yellow,
            thresholds.wape_relative_red,
        ),
        "bias_status": _status(
            abs(float(current.get("bias", np.nan))),
            thresholds.absolute_bias_yellow,
            thresholds.absolute_bias_red,
        ),
    }
    if "coverage" in current:
        statuses["coverage_status"] = _status(
            abs(float(current["coverage"]) - 0.80),
            thresholds.coverage_deviation_yellow,
            thresholds.coverage_deviation_red,
        )
    if "interval_width" in current and "interval_width" in reference:
        ref_width = float(reference["interval_width"])
        ratio = float(current["interval_width"]) / ref_width if ref_width > 0 else np.nan
        statuses["width_status"] = _status(
            ratio,
            thresholds.width_ratio_yellow,
            thresholds.width_ratio_red,
        )
    overall = max(statuses.values(), key=lambda s: STATUS_ORDER[s])
    return {**statuses, "overall_status": overall, "wape_relative_degradation": wape_degradation}
