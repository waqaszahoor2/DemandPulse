# DemandPulse Rollback Strategy

## Application rollback

Every deployed image is tagged by Git commit SHA. Cloud Run creates an immutable revision per deployment.

Before production deployment, `.github/workflows/deploy.yml` captures the currently serving revision. If the post-deploy smoke test fails, the workflow restores 100% traffic to that revision.

Manual rollback:

```bash
gcloud run revisions list \
  --service="$CLOUD_RUN_PRODUCTION_SERVICE" \
  --region="$GCP_REGION"

gcloud run services update-traffic "$CLOUD_RUN_PRODUCTION_SERVICE" \
  --region="$GCP_REGION" \
  --to-revisions="PREVIOUS_REVISION=100"
```

Never rebuild an old commit just to roll back when the previous immutable Cloud Run revision already exists.

## Model rollback

MLflow uses aliases:

```text
champion
candidate
previous_champion
```

Promotion stores the prior champion as `previous_champion`. If champion v5 creates unacceptable forecast/calibration behavior:

1. route Cloud Run traffic back if application code also changed;
2. call the registry rollback helper or set the `champion` alias back to v4;
3. export v4's serving bundle to an immutable Cloud Storage prefix if not already present;
4. update `PRODUCTION_MODEL_BUNDLE_URI` to the v4 bundle;
5. redeploy the same application image if only the model changes;
6. verify `/ready`, `/model/info`, point and probabilistic smoke predictions;
7. document the incident and freeze v5 from further promotion until investigated.

Python helper:

```python
from demandpulse.mlops.registry import rollback_champion
rollback_champion("demandpulse-point-forecast")
```

Do not delete the failed model version; retain it for lineage and incident analysis.

## Rollback triggers

Rollback rather than retrain when the problem is deployment-specific:

- model fails to load;
- request schema/feature contract is incompatible;
- 5xx/error rate jumps after a new revision;
- latency or memory becomes unsafe;
- immediate severe calibration/forecast regression is linked to the new model/revision.

Retraining is a slower model-development decision, not an incident-response substitute.
