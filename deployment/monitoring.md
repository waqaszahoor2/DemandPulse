# DemandPulse Production Monitoring

## Observability model

Cloud Run already exports platform request, container and system logs/metrics. DemandPulse adds JSON application logs, request IDs, bounded application latency statistics, model-version fields and prediction-distribution events.

### API signals

Track:

- request count;
- HTTP status counts;
- 5xx/error rate;
- P50/P95/P99 latency;
- container instance count/restarts;
- CPU and memory utilization;
- request concurrency.

`GET /internal/metrics` exposes bounded low-cardinality in-process aggregates when `METRICS_ENABLED=true`. Production can disable that endpoint and rely on Cloud Monitoring/log-based metrics instead.

### ML signals

Prediction events contain only:

```text
prediction_id
request_id
timestamp
store_id
product_id
forecast_date
horizon
p10
p50
p90
model_version
```

No historical feature payload or actual future target is written into the prediction log.

Structured prediction logs should be routed with a **Cloud Logging sink** into BigQuery or Cloud Storage for durable monitoring. Local Parquet output (`PREDICTION_LOG_PARQUET`) is intended for development/batch validation, not Cloud Run persistence.

## Actual outcome ingestion

Actuals arrive later as a separate immutable dataset:

```text
store_id
product_id
date
actual_sales
```

`demandpulse.monitoring.outcomes` validates these records and joins them to immutable predictions on:

```text
(store_id, product_id, forecast_date)
```

That matched table becomes the source for production MAE, WAPE, Bias, pinball loss, interval coverage and interval width.

## Performance slices

Monitor by:

- model version;
- forecast horizon;
- store;
- product/category where sample size is sufficient (join the immutable prediction log to a versioned product/category dimension);
- demand segment;
- promotion/holiday status where scientifically appropriate.

Avoid alerting on tiny groups with unstable denominators.

## Drift monitoring

Use the existing `demandpulse.monitoring` functions to compare a fixed training/reference window against recent production data:

- numeric: PSI + two-sample KS;
- categorical: PSI + total-variation/new-category rate;
- missingness changes;
- new stores/products;
- target mean/variance/zero-sales/intermittency after actuals arrive;
- prediction distribution and P10–P90 width drift before actuals arrive.

Reference distributions must be versioned with the model so a deployment can be reproduced.

## GREEN / YELLOW / RED

Thresholds are configuration policy, not universal statistical truths.

- **GREEN:** data, performance and calibration within configured tolerances.
- **YELLOW:** moderate drift, increasing latency, early degradation or calibration movement; investigate, do not automatically retrain.
- **RED:** severe data incident, repeated 5xx/model-load failure, persistent forecast degradation, severe bias or interval-calibration failure.

`demandpulse.monitoring.alerts` and `demandpulse.monitoring.retraining` provide configurable policy helpers.

## Retraining rule

A single PSI/KS change is not enough. Candidate retraining should require:

1. acceptable incoming data quality;
2. sufficient new labelled observations;
3. performance/calibration degradation that persists over multiple monitoring periods;
4. meaningful drift when it helps explain the degradation.

The output is `RETRAIN_CANDIDATE`, not automatic champion promotion.

## Candidate evaluation and promotion

```text
Champion
  ↓
New labelled data
  ↓
Candidate training
  ↓
Chronological evaluation
  ↓
Accuracy + Bias + Calibration + Data Quality + Tests
  ↓
Candidate alias
  ↓ explicit approval
Champion alias
```

`demandpulse.mlops.registry.promote_candidate(..., apply=False)` is dry-run by default. Explicit `apply=True` is required, and the previous champion is saved to `previous_champion` before promotion.

## Suggested alerts

Create Cloud Monitoring alert policies for sustained conditions rather than single samples:

- service unavailable or readiness failures;
- 5xx error-rate spike;
- P95 latency above the environment threshold for multiple windows;
- container restarts/model hydration failure;
- severe PSI/new-category drift for repeated monitoring runs;
- WAPE degradation relative to the champion reference;
- absolute Bias outside policy bounds;
- P10–P90 coverage deviation beyond the calibrated tolerance.

Alerts should link to `deployment/runbook.md`.
