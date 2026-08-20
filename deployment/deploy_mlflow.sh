#!/usr/bin/env bash
set -euo pipefail

: "${GCP_PROJECT_ID:?required}"
: "${GCP_REGION:?required}"
: "${MLFLOW_CLOUD_RUN_SERVICE:?required}"
: "${MLFLOW_IMAGE:?required}"
: "${MLFLOW_RUNTIME_SERVICE_ACCOUNT:?required}"
: "${MLFLOW_CLOUDSQL_INSTANCE:?required}"
: "${MLFLOW_BACKEND_STORE_URI_SECRET:?required}"
: "${MLFLOW_ARTIFACT_ROOT:?required}"

gcloud run deploy "${MLFLOW_CLOUD_RUN_SERVICE}" \
  --project "${GCP_PROJECT_ID}" \
  --region "${GCP_REGION}" \
  --image "${MLFLOW_IMAGE}" \
  --service-account "${MLFLOW_RUNTIME_SERVICE_ACCOUNT}" \
  --command python \
  --args=-m,demandpulse.mlops.server \
  --port 5000 \
  --cpu "${MLFLOW_CPU:-1}" \
  --memory "${MLFLOW_MEMORY:-1Gi}" \
  --concurrency "${MLFLOW_CONCURRENCY:-20}" \
  --timeout 60s \
  --min "${MLFLOW_MIN_INSTANCES:-0}" \
  --max "${MLFLOW_MAX_INSTANCES:-3}" \
  --set-cloudsql-instances "${MLFLOW_CLOUDSQL_INSTANCE}" \
  --set-secrets "MLFLOW_BACKEND_STORE_URI=${MLFLOW_BACKEND_STORE_URI_SECRET}:latest" \
  --set-env-vars "MLFLOW_ARTIFACT_ROOT=${MLFLOW_ARTIFACT_ROOT},MLFLOW_ALLOWED_HOSTS=${MLFLOW_ALLOWED_HOSTS:-*.run.app}" \
  --startup-probe "httpGet.path=/health,httpGet.port=5000,periodSeconds=5,timeoutSeconds=2,failureThreshold=24" \
  --liveness-probe "httpGet.path=/health,httpGet.port=5000,periodSeconds=30,timeoutSeconds=3,failureThreshold=3" \
  --no-allow-unauthenticated \
  --quiet

URL=$(gcloud run services describe "${MLFLOW_CLOUD_RUN_SERVICE}" \
  --project "${GCP_PROJECT_ID}" \
  --region "${GCP_REGION}" \
  --format='value(status.url)')

echo "MLflow deployed at: ${URL}"
echo "Access requires an authorized Cloud Run identity token."
