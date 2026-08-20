from __future__ import annotations

import pandas as pd

from demandpulse.monitoring.alerts import evaluate_alerts
from demandpulse.monitoring.outcomes import join_predictions_with_actuals, validate_actual_outcomes
from demandpulse.monitoring.retraining import RetrainingPolicy, decide_retraining
from demandpulse.monitoring.telemetry import TelemetryStore


def test_readiness_endpoint_and_request_id(client):
    response = client.get("/ready", headers={"X-Request-ID": "trace-123"})
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.headers["X-Request-ID"] == "trace-123"


def test_internal_metrics_tracks_latency_and_predictions(client, valid_forecast_payload):
    assert client.post("/forecast", json=valid_forecast_payload).status_code == 200
    metrics = client.get("/internal/metrics")
    assert metrics.status_code == 200
    body = metrics.json()
    assert body["request_count"] >= 1
    assert body["latency_ms"]["p95"] is not None
    assert body["predictions"]["point.prediction"]["count"] >= 1


def test_telemetry_store_is_bounded_and_low_cardinality():
    store = TelemetryStore(max_samples=3)
    for i in range(5):
        store.record_request("/forecast", 200, float(i))
        store.record_prediction("point", prediction=float(i))
    snap = store.snapshot()
    assert snap["request_count"] == 5
    assert snap["latency_ms"]["count"] == 3
    assert snap["predictions"]["point.prediction"]["count"] == 3


def test_actual_outcomes_join_preserves_prediction_keys():
    predictions = pd.DataFrame({
        "store_id": [1],
        "product_id": [10],
        "forecast_date": ["2026-08-21"],
        "horizon": [1],
        "p50": [12.0],
        "model_version": ["v1"],
    })
    actuals = pd.DataFrame({
        "store_id": [1],
        "product_id": [10],
        "date": ["2026-08-21"],
        "actual_sales": [11.0],
    })
    joined = join_predictions_with_actuals(predictions, actuals)
    assert len(joined) == 1
    assert joined.iloc[0]["actual_sales"] == 11.0
    assert predictions.iloc[0]["forecast_date"] == "2026-08-21"


def test_actual_outcomes_reject_duplicates():
    actuals = pd.DataFrame({
        "store_id": [1, 1],
        "product_id": [10, 10],
        "date": ["2026-08-21", "2026-08-21"],
        "actual_sales": [11.0, 12.0],
    })
    try:
        validate_actual_outcomes(actuals)
    except ValueError as exc:
        assert "duplicate" in str(exc).lower()
    else:
        raise AssertionError("duplicate actual outcomes must be rejected")


def test_retraining_requires_persistent_degradation_and_labels():
    history = [
        {"degraded": True, "meaningful_drift": True, "calibration_failure": False},
        {"degraded": True, "meaningful_drift": True, "calibration_failure": False},
    ]
    result = decide_retraining(
        history,
        new_observations=6000,
        data_quality_ok=True,
        policy=RetrainingPolicy(min_new_observations=5000, persistence_periods=2),
    )
    assert result["decision"] == "RETRAIN_CANDIDATE"

    drift_only = decide_retraining(
        [
            {"degraded": False, "meaningful_drift": True, "calibration_failure": False},
            {"degraded": False, "meaningful_drift": True, "calibration_failure": False},
        ],
        new_observations=6000,
        data_quality_ok=True,
    )
    assert drift_only["decision"] == "NO_RETRAIN"


def test_alerts_escalate_only_meaningful_signals():
    alerts = evaluate_alerts({"error_rate": 0.01, "latency_p95_ms": 200, "max_psi": 0.3})
    assert alerts["api_error_rate"] == "GREEN"
    assert alerts["api_latency"] == "GREEN"
    assert alerts["feature_drift"] == "RED"


def test_target_drift_summary_tracks_level_variance_and_zero_rate():
    from demandpulse.monitoring.production import target_drift_summary

    report = target_drift_summary([0, 1, 2, 0], [0, 0, 4, 4])
    assert report["recent_mean"] != report["reference_mean"]
    assert report["recent_variance"] != report["reference_variance"]
    assert report["recent_zero_sales_rate"] == 0.5
