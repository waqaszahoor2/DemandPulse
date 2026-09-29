"""Production retraining policy based on persistent evidence, not single drift events."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class RetrainingPolicy:
    """Configurable retraining gates."""

    min_new_observations: int = 5000
    persistence_periods: int = 2
    require_performance_degradation: bool = True
    allow_drift_with_degradation: bool = True


def decide_retraining(
    history: Iterable[Mapping[str, object]],
    *,
    new_observations: int,
    data_quality_ok: bool,
    policy: RetrainingPolicy = RetrainingPolicy(),
) -> dict[str, object]:
    """Return a transparent retraining decision from recent monitoring periods.

    Each history item can include boolean `degraded`, `meaningful_drift`, and
    `calibration_failure` signals. Evidence must persist across the configured number
    of most recent periods. A data-quality incident blocks retraining.
    """
    rows = list(history)
    if not data_quality_ok:
        return {"decision": "BLOCK", "reason": "data quality is not acceptable", "persistent": False}
    if new_observations < policy.min_new_observations:
        return {
            "decision": "NO_RETRAIN",
            "reason": "insufficient new labelled observations",
            "persistent": False,
        }
    if len(rows) < policy.persistence_periods:
        return {"decision": "NO_RETRAIN", "reason": "insufficient monitoring history", "persistent": False}

    recent = rows[-policy.persistence_periods :]
    degraded = all(bool(row.get("degraded", False)) for row in recent)
    drift = all(bool(row.get("meaningful_drift", False)) for row in recent)
    calibration = all(bool(row.get("calibration_failure", False)) for row in recent)
    persistent = degraded or calibration or (degraded and drift)

    if policy.require_performance_degradation and not (degraded or calibration):
        return {
            "decision": "NO_RETRAIN",
            "reason": "drift without persistent performance/calibration degradation",
            "persistent": drift,
        }
    if persistent and (degraded or calibration or (policy.allow_drift_with_degradation and drift)):
        return {
            "decision": "RETRAIN_CANDIDATE",
            "reason": "persistent degradation/calibration evidence with sufficient new labels",
            "persistent": True,
        }
    return {"decision": "NO_RETRAIN", "reason": "retraining criteria not satisfied", "persistent": False}
