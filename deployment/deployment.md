# DemandPulse Cloud Deployment

## Selected platform: Google Cloud Run

DemandPulse uses **Google Cloud Run** for the serving tier and **Google Artifact Registry** for immutable container images. Cloud Run is a good fit because DemandPulse is already a stateless HTTP container, LightGBM inference is CPU-friendly, the service benefits from managed HTTPS/autoscaling, and the project does not need Kubernetes-level control.

The deployment intentionally keeps the API independent from the MLflow tracking server at request time:

```text
GitHub
  ↓
GitHub Actions + Workload Identity Federation
  ↓
Artifact Registry
  ↓
Cloud Run: DemandPulse API
  ↓
Immutable model bundle in Cloud Storage

Training / model governance
  ↓
MLflow Model Registry
  ↓
Approved champion export
  ↓
Cloud Storage model bundle
```

This means an MLflow outage does not make the prediction API unavailable. The API downloads the approved champion bundle during startup and `/ready` stays `503` until required models are loaded.

## Environments

Use separate GitHub Environments and Cloud Run services:

| Environment | Cloud Run service | Purpose |
|---|---|---|
| development | local/Docker Compose | developer testing |
| staging | `demandpulse-api-staging` | deployment and smoke validation |
| production | `demandpulse-api-prod` | production traffic |

Production should require a GitHub Environment reviewer before the `production` job can run.

## Required Google Cloud resources

Create once per GCP project/region:

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  iamcredentials.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com

gcloud artifacts repositories create demandpulse \
  --repository-format=docker \
  --location="$REGION"

gcloud storage buckets create "gs://$MODEL_BUCKET" --location="$REGION" --uniform-bucket-level-access
gcloud storage buckets create "gs://$MLFLOW_ARTIFACT_BUCKET" --location="$REGION" --uniform-bucket-level-access
```

For production MLflow metadata, use a managed PostgreSQL backend (for example Cloud SQL) and Cloud Storage for artifacts. SQLite on the Cloud Run filesystem is not persistent and should not be used for production metadata.

## Workload Identity Federation

GitHub Actions authenticates with short-lived Workload Identity Federation credentials. Do not store service-account JSON keys in GitHub.

Repository/Environment variables used by `.github/workflows/deploy.yml`:

```text
GCP_PROJECT_ID
GCP_REGION
GCP_WORKLOAD_IDENTITY_PROVIDER
GCP_DEPLOY_SERVICE_ACCOUNT
GAR_REPOSITORY
CLOUD_RUN_RUNTIME_SERVICE_ACCOUNT
CLOUD_RUN_STAGING_SERVICE
CLOUD_RUN_PRODUCTION_SERVICE
STAGING_MODEL_BUNDLE_URI
PRODUCTION_MODEL_BUNDLE_URI
SMOKE_FORECAST_PAYLOAD
```

`SMOKE_FORECAST_PAYLOAD` should contain a non-sensitive, representative JSON feature vector that is valid for the currently deployed feature contract.

## IAM separation

Use separate identities:

- **GitHub deploy service account:** Artifact Registry writer, Cloud Run deploy permissions, and permission to act as the runtime service account.
- **Cloud Run runtime service account:** read-only access to the model bucket and only the Google services the API needs.
- **MLflow service account:** access to its artifact bucket and database connection only.

Follow least privilege; do not grant project Owner/Editor for convenience.

## Champion model bundle

After a candidate passes evaluation and the MLflow `champion` alias is deliberately updated, export the serving artifacts into an immutable model bundle. Create checksums before upload:

```bash
python scripts/create_model_manifest.py models/
gcloud storage rsync --recursive models/ "gs://$MODEL_BUCKET/champions/$MODEL_VERSION/"
```

Set the environment-specific `MODEL_BUNDLE_URI` to the immutable prefix, for example:

```text
gs://demandpulse-models/champions/5
```

Do not point production at a mutable `latest/` directory.

## Cloud Run serving configuration

The deployment workflow uses these safety properties:

- production Uvicorn without `--reload`;
- startup probe on `/ready`;
- liveness probe on `/health`;
- request timeout below the Cloud Run timeout;
- fixed request-body size limit;
- configurable CPU, memory, concurrency, minimum and maximum instances;
- non-root container user;
- Cloud Run IAM authentication by default;
- immutable image tag based on Git commit SHA;
- model version supplied independently through `MODEL_BUNDLE_URI`.

Cloud Run injects `PORT`; DemandPulse accepts both `PORT` and local `API_PORT`.

## MLflow in cloud

MLflow should be deployed as a **separate operator/training service**, not on the API request path.

Recommended production state:

```text
MLflow Cloud Run service
├── backend store: managed PostgreSQL / Cloud SQL
└── artifact store: gs://<mlflow-artifact-bucket>
```

Keep the MLflow service IAM-authenticated. Operators can access it through authenticated Cloud Run access/proxying rather than making the registry UI anonymously public.

A parameterized launcher is included:

```bash
export GCP_PROJECT_ID=...
export GCP_REGION=...
export MLFLOW_CLOUD_RUN_SERVICE=demandpulse-mlflow
export MLFLOW_IMAGE=<artifact-registry-image-by-sha>
export MLFLOW_RUNTIME_SERVICE_ACCOUNT=...
export MLFLOW_CLOUDSQL_INSTANCE=project:region:instance
export MLFLOW_BACKEND_STORE_URI_SECRET=mlflow-backend-uri
export MLFLOW_ARTIFACT_ROOT=gs://<mlflow-artifact-bucket>
./deployment/deploy_mlflow.sh
```

The database URI is read from Secret Manager and is never embedded in the repository.

The API can continue serving an already-hydrated champion model if MLflow is temporarily unavailable.

## CI/CD deployment flow

```text
Push to main
  ↓
Quality gate: lint + format + types + tests + security
  ↓
Build image tagged with Git SHA + semantic version
  ↓
Trivy image vulnerability scan
  ↓
Push to Artifact Registry
  ↓
Deploy staging
  ↓
/health + /ready + /model/info + /forecast smoke tests
  ↓
Lightweight 1/10/50 concurrency staging load check
  ↓
GitHub production environment approval
  ↓
Capture previous Cloud Run revision
  ↓
Deploy production
  ↓
Smoke test
  ↓
Automatic traffic rollback if the production smoke test fails
```

## HTTPS

Cloud Run provides a managed HTTPS URL. If a custom domain is required later, attach it through supported Cloud Run/domain or load-balancer configuration without changing the application container. The supplied deployment keeps the Cloud Run invoker IAM check enabled; clients must be explicitly authorized.

## Request-rate strategy

DemandPulse does **not** implement a per-instance in-memory rate limiter because Cloud Run can run many instances, making such limits inconsistent. Use Cloud Run max instances/concurrency for capacity protection and add API Gateway/Cloud Armor rate limiting if the service becomes externally exposed to untrusted high-volume clients.

## Cost drivers

Do not estimate a fixed monthly bill without traffic/resource data. Primary cost drivers are:

- request volume and request duration;
- configured CPU/memory per instance;
- minimum instances (reduced cold starts but continuous cost);
- maximum concurrent traffic and autoscaling;
- model-bundle and prediction-log storage;
- Cloud Logging/Monitoring volume and retention;
- MLflow artifact storage;
- managed PostgreSQL/Cloud SQL for MLflow metadata;
- scheduled monitoring/retraining jobs.

Measure real staging traffic before selecting production minimum instances and concurrency.
