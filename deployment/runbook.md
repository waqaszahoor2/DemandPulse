# DemandPulse Production Runbook

## 1. Service unavailable

1. Check Cloud Run service/revision status and recent deploy history.
2. Query `/health`; if it fails, inspect Cloud Run container/system logs.
3. Check container restarts, memory, CPU and startup-probe failures.
4. If tied to the latest revision, roll traffic back to the previous revision.
5. Do not retrain a model to fix an application/runtime outage.

## 2. `/health` works but `/ready` is 503

1. Inspect JSON logs for `model_bundle_hydration_failed` or model-load warnings.
2. Verify `MODEL_BUNDLE_URI` points to an immutable existing bundle.
3. Verify the runtime service account has read-only access to the model bucket.
4. Verify `model_manifest.json` checksums and required `point,probabilistic` artifacts.
5. Roll back to the previous model-bundle URI/revision if the new bundle is defective.

## 3. MLflow unavailable

Serving should remain available because the API loads a pre-exported champion bundle from Cloud Storage.

1. Confirm API `/ready` remains healthy.
2. Pause training/model promotion operations.
3. Check MLflow Cloud Run, Cloud SQL and artifact bucket health.
4. Restore MLflow before new model registration/promotion; do not bypass registry governance.

## 4. High 5xx/error rate

1. Filter structured logs by request ID and endpoint.
2. Determine whether failures are validation 4xx, model 503, timeout 504 or unexpected 500.
3. Compare onset with a deployment/model-version change.
4. Roll back a bad revision/model if correlated.
5. Escalate only sustained error-rate thresholds; avoid paging on isolated client mistakes.

## 5. High latency

1. Compare P50/P95/P99 latency and Cloud Run CPU/memory/concurrency.
2. Check cold starts and model hydration times.
3. Reduce concurrency if CPU saturation causes queuing; increase CPU/memory only after measurement.
4. Consider a small production minimum instance count for latency-sensitive traffic.
5. Run the staging load script before changing production resources.

## 6. Severe drift

1. Validate data quality and schema before interpreting drift.
2. Identify whether drift is feature, category, target or prediction drift.
3. Check if forecast WAPE/Bias/calibration also degraded after actuals arrived.
4. YELLOW drift alone means investigate—not retrain.
5. Use the persistence/minimum-label retraining decision before candidate training.

## 7. Failed deployment

1. GitHub workflow automatically attempts traffic rollback when production smoke tests fail.
2. Verify traffic now points to the captured prior revision.
3. Compare build SHA, model bundle URI and environment configuration.
4. Fix forward in staging; do not bypass the production environment approval gate.

## 8. Manual rollback

Use `deployment/rollback.md`. Confirm after rollback:

```text
/health -> 200
/ready -> 200
/model/info -> expected model version
/forecast -> numeric non-negative prediction
/forecast/probabilistic -> P10 <= P50 <= P90
```

## 9. Security incident

1. Disable/rotate the affected secret or identity binding in Secret Manager/IAM.
2. Revoke compromised GitHub environment access if relevant.
3. Redeploy only after CI/security gates pass.
4. Never paste secrets into logs, issues, commits or model metadata.
