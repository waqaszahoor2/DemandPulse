# DemandPulse

## Production-Oriented Retail Demand Intelligence Platform

[![CI Quality Gates](https://github.com/waqaszahoor2/DemandPulse/actions/workflows/ci.yml/badge.svg)](https://github.com/waqaszahoor2/DemandPulse/actions)
[![Docker Build](https://github.com/waqaszahoor2/DemandPulse/actions/workflows/docker.yml/badge.svg)](https://github.com/waqaszahoor2/DemandPulse/actions)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

DemandPulse is an end-to-end, production-grade retail demand intelligence platform. It transforms raw e-commerce streaming data into expected demand forecasts, uncertainty quantification bounds, observational causal promotion lift estimates, structurally reconciled hierarchical accounting totals, and cost-optimal inventory decisions.

---

## 1. Quick Overview

### What problem does DemandPulse solve?
Retail demand planning requires answering distinct operational questions that standard single-point forecasts cannot solve alone:
- **Expected Demand**: How many units of SKU $X$ will store $Y$ sell next week?
- **Uncertainty & Risk**: What is the P10–P90 downside/upside variance for safety stock allocation?
- **Causal Impact**: Did a promotional discount *cause* incremental demand, or was it merely correlated with baseline sales?
- **Accounting Coherence**: Do individual product forecasts sum coherently to category, store, city, and enterprise totals?
- **Inventory Action**: What order quantity minimizes expected holding costs and stockout penalties?

### Why does it matter?
Sub-optimal demand planning leads directly to billions in annual retail losses through stockouts (lost revenue) and overstocking (capital tie-up and waste). DemandPulse connects statistical machine learning with decision science to provide auditable, cost-aware operational recommendations.

### What makes it technically advanced?
- **Global LightGBM Gradient Boosting**: Single model trained across cross-series hierarchies with temporal feature sharing.
- **Conformalized Quantile Forecasting**: Guarantees finite-sample coverage for P10/P50/P90 prediction intervals without distributional assumptions.
- **Doubly Robust Causal Inference**: AIPW (Augmented Inverse Propensity Weighting) estimator separating true promotional lift from selection bias.
- **MinT Hierarchical Reconciliation**: Minimum Trace shrinkage matrix projection enforcing 100% accounting coherence.
- **Production MLOps & Observability**: Sub-10ms FastAPI serving, MLflow model registry governance, automated drift monitoring (PSI/KS), persistent retraining policy, and Google Cloud Run deployment automation.

### Tech Stack
`Python 3.11` • `LightGBM` • `FastAPI` • `MLflow` • `Docker` • `Conformal Prediction` • `CausalML / SciPy` • `Google Cloud Run` • `GitHub Actions CI/CD` • `Pytest`

---

## 2. Project Highlights

### Forecasting
* **Global LightGBM Model**: Trained across cross-series store/product hierarchies with non-negative operational prediction constraints.
* **Rolling-Origin Backtesting**: Leakage-free chronological validation folds preserving strict temporal ordering.
* **Leakage-Safe Feature Pipeline**: Shift-based lag features ($t-1, t-7, t-14$) and rolling window statistics ($7, 14$ days).

### Uncertainty & Calibration
* **Direct Quantile Regression**: Independent models estimating P10, P50, and P90 demand bounds.
* **Conformal Interval Calibration**: Non-parametric post-hoc calibration ensuring exact nominal coverage.
* **Interval Diagnostics**: Automated evaluation of Pinball Loss, empirical coverage rates, and interval score.

### Causal Inference
* **Propensity Score Modeling**: Logistic and tree-based propensity estimation rejecting post-treatment colliders.
* **Inverse Propensity Weighting (IPW)**: Weighting samples to control for promotional selection bias.
* **Doubly Robust AIPW**: Combines propensity scores and outcome regressions for robust ATE/ATT/CATE estimation.
* **Placebo & Sensitivity Checks**: Pseudo-treatment checks and E-value sensitivity bounds validating causal robustness.

### Decision Intelligence
* **Cost-Aware Inventory Optimization**: Translates forecast quantiles into exact Safety Stock, Reorder Points, and Order Quantities.
* **Stockout-Risk Simulation**: Monte Carlo evaluation under holding cost ($C_h$) and stockout penalty ($C_s$) regimes.
* **Service Level Alignment**: Configurable target fill-rate optimization (e.g., 95% or 99% service levels).

### Production MLOps & Architecture
* **FastAPI Serving Layer**: Lifespan model caching, sub-10ms execution, Uvicorn ASGI server, structured JSON telemetry.
* **MLflow Tracking & Registry**: Local and cloud tracking, model artifact storage, dry-run candidate vs. champion promotion gates.
* **Containerization**: Non-root, multi-stage Docker build producing lightweight production images.
* **Production Observability**: Real-time PSI & KS data drift detection, prediction logging, outcome joining, and persistent retraining logic.
* **Cloud Deployment Path**: Automated staging-to-production deployment pipeline targeting Google Cloud Run via Workload Identity Federation.

---

## 3. Recruiter Summary Results Table

> All reported metrics are exact empirical results from executed backtests on `FreshRetailNet-50K`. See [`RESULTS.md`](RESULTS.md) for full benchmarks.

| Capability | Method | Main Empirical Result | Baseline Comparison | Strategic Impact |
| :--- | :--- | :---: | :---: | :--- |
| **Point Forecasting** | Global LightGBM | **WAPE: 0.1984** | Seasonal Naive: 0.4281 | **53.6% error reduction** over baseline |
| **Uncertainty Quantification** | Conformal Quantiles | **Coverage: 80.4%** | Uncalibrated: 74.2% | Restores exact 80% nominal coverage bound |
| **Causal Promotion Lift** | Doubly Robust AIPW | **ATE: +8.32 units** | Naive Difference: +12.40 | Eliminates **49% selection bias** overstatement |
| **Hierarchical Consistency** | MinT Reconciliation | **Coherence Error: 0.00** | Unreconciled: 14.82 | Achieves **100% accounting coherence** |
| **Inventory Optimization** | Uncertainty Policy (P90) | **Expected Cost: $540** | Fixed Order Policy: $1,420 | **61.9% reduction in total inventory costs** |

---

## 4. System Architecture

```text
FreshRetailNet-50K
        ↓
Data Ingestion
        ↓
Validation
        ↓
Feature Engineering
        ↓
┌───────────────┬─────────────────┬────────────────┐
↓               ↓                 ↓
Point        Probabilistic      Hierarchical
Forecast     Forecasting        Forecasting
↓               ↓                 ↓
└───────────────┴─────────────────┘
                ↓
        Causal Promotion Engine
                ↓
        Inventory Optimization
                ↓
              FastAPI
                ↓
              MLflow
                ↓
           Docker / Cloud
                ↓
       Production Monitoring
                ↓
          Drift Detection
                ↓
       Retraining Decision
```

*For detailed component breakdowns, data flows, and training/inference sequence diagrams, see [`ARCHITECTURE.md`](ARCHITECTURE.md).*

---

## 5. System Documentation Navigation

- 📐 [**ARCHITECTURE.md**](ARCHITECTURE.md) — System flow, component responsibilities, data flow, training & inference sequences.
- 📊 [**RESULTS.md**](RESULTS.md) — Full empirical benchmark metrics, quantile evaluations, causal tables, and research answers.
- 🎴 [**MODEL_CARD.md**](MODEL_CARD.md) — Intended use, feature definitions, hyperparameter configurations, failure modes, and limits.
- 🎴 [**DATA_CARD.md**](DATA_CARD.md) — `FreshRetailNet-50K` schema, streaming hash sampling, stockout censoring, and privacy.
- 🤝 [**CONTRIBUTING.md**](CONTRIBUTING.md) — Environment setup, `ruff` linting, `mypy` typing, `pytest` coverage, and PR workflows.
- 🎓 [**Interview Notes**](docs/interview_notes.md) — Senior-level technical Q&A covering LightGBM, WAPE, AIPW, Conformal prediction, etc.

---

## 6. Business Value & Decision Science

DemandPulse directly impacts core retail operating metrics:

1. **Optimized Inventory Replenishment**: Replaces crude historical averages with dynamic, lead-time demand distributions.
2. **Stockout Mitigation**: Reduces out-of-stock events from 14.8% to 2.1% through P90 uncertainty safety stock buffer sizing.
3. **Overstock Reduction**: Prevents capital tie-up in slow-moving SKUs by bounding upside P90 demand limits.
4. **True Promotional ROI**: Identifies which product promotions drive genuine incremental lift (+8.32 units) versus those that subsidize sales that would have happened anyway.
5. **Multi-Level Alignment**: Reconciles product-level store forecasts with executive category and regional revenue projections.

---

## 7. Key Technical Rationale

- **Why Chronological Validation?** Time-series data exhibits temporal autocorrelation. Random train/test splits cause future data leakage. Chronological rolling-origin backtesting ensures realistic out-of-sample evaluation.
- **Why Global LightGBM?** Rather than fitting 50,000 individual ARIMA models, a single global LightGBM model learns shared cross-series temporal patterns while remaining computationally fast and scalable.
- **Why Conformal Prediction?** Raw quantile regressions often suffer from empirical undercoverage. Conformal calibration provides mathematically sound coverage guarantees without assuming Gaussian residual distributions.
- **Why Doubly Robust AIPW?** Promotional assignment in retail is non-random (high-volume SKUs receive more promotions). AIPW combines propensity weighting and outcome regression to produce unbiased causal treatment effect estimates.
- **Why MinT Reconciliation?** Unreconciled forecasts lead to store-level demand sums that mismatch city and corporate budgets. MinT projection achieves zero coherence error while minimizing forecast error variance across the hierarchy.

---

## 8. Failure Analysis: What Did Not Work Perfectly

A production-grade system must transparently document its scientific and technical boundaries:

1. **Intermittent / Sparse Demand**: Long-tail SKUs with high zero-demand frequency ($>60\%$ zero days) exhibited higher relative WAPE error (0.34) compared to fast-moving SKUs (0.15).
2. **Cold-Start SKUs**: Products with $<14$ days of sales history lack required lag features, requiring initial fallback to category-level median estimates.
3. **Stockout Censoring**: Historical sales data reflects realized sales, not unconstrained demand. On zero-stock days, observed demand is artificially capped, slightly biasing baseline lag means downward.
4. **Promotional Overlap Confounding**: SKUs experiencing concurrent price discounts, holiday surges, and endcap displays make isolating single-factor causal lift challenging.
5. **Conformal Width Expansion**: Restoring coverage from 74.2% to 80.4% via conformal adjustment expanded average interval width by 13.6%, slightly increasing holding cost allocation for high-variance products.

---

## 9. Reproducibility & Quickstart

### Prerequisites
- Python 3.10+ (Python 3.11 recommended)
- Git & Docker

### 1. Clone & Install
```bash
git clone https://github.com/waqaszahoor2/DemandPulse.git
cd DemandPulse
python -m pip install -e ".[dev]"
```

### 2. Run All Research Notebooks (Offline Pipeline)
```bash
python scripts/run_all_notebooks.py
```
Executes notebooks `01` through `07` sequentially in fresh kernels, preserves outputs, saves executed notebooks to `notebooks/executed/`, and outputs `reports/notebook_execution_report.json`.

### 3. Run Test Suite (64 Passed)
```bash
pytest -v
```

### 4. Audit Model Bundle Sizes & Validate Deployment
```bash
python scripts/audit_models.py
python scripts/validate_deployment.py
```

### 5. Local Vercel Serverless Development
```bash
vercel dev
```

### 6. Production Vercel Deployment
```bash
vercel --prod
```

### Serverless Architecture Rationale
- **Offline Pipeline**: Data materialization from `FreshRetailNet-50K`, model training, cross-validation, conformal calibration, and notebook execution run strictly offline.
- **Vercel Serverless Inference**: Vercel functions (`api/index.py`) serve sub-10ms predictions using cached model artifacts under `models/` without bundling heavy datasets or notebook runners into serverless packages.

### 7. Launch Docker Stack (Alternative Container Host)
```bash
docker compose up --build
```
This boots the FastAPI service on `http://localhost:8000` and MLflow tracking server on `http://localhost:5000`.

---

## 10. API Serving & Demo

### OpenAPI Interactive Documentation
Once launched, open `http://localhost:8000/docs` to inspect the interactive Swagger UI.

### System Endpoints
- `GET /health` — Liveness check (`200 OK`)
- `GET /ready` — Model readiness check (`200 OK`)
- `GET /model/info` — Safe model version & performance metadata
- `POST /forecast` — Point demand forecast
- `POST /forecast/probabilistic` — P10/P50/P90 quantile forecast with conformal interval
- `POST /promotion-effect` — Observational causal lift estimate
- `POST /inventory/recommendation` — Cost-aware reorder recommendation

### Example Curl Request (Point Forecast)

```bash
curl -X POST "http://localhost:8000/forecast" \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "STORE_001",
    "product_id": "PROD_042",
    "city": "CITY_01",
    "category_id": "CAT_10",
    "date": "2024-03-15",
    "price": 12.99,
    "discount": 0.10,
    "promotion": 1,
    "lag_1": 14.0,
    "lag_7": 12.0,
    "lag_14": 15.0,
    "rolling_mean_7": 13.5,
    "rolling_std_7": 1.8
  }'
```

### Example Response JSON

```json
{
  "prediction": 14.82,
  "store_id": "STORE_001",
  "product_id": "PROD_042",
  "date": "2024-03-15",
  "model_version": "point-lgbm-v1.2.0",
  "timestamp": "2026-08-20T10:00:00Z"
}
```

---

## 11. Recruiter & Portfolio Assets

### Repository Topics
`data-science` • `machine-learning` • `time-series` • `forecasting` • `causal-inference` • `mlops` • `fastapi` • `lightgbm` • `probabilistic-forecasting` • `inventory-optimization` • `mlflow` • `docker`

### Short GitHub Repository Description (<150 chars)
> Retail demand intelligence platform featuring LightGBM forecasting, conformal prediction bounds, causal AIPW promotion lift, and FastAPI MLOps serving.

### Pin-Worthy Profile README Summary (2–3 Lines)
> **DemandPulse**: Production retail demand intelligence system integrating global LightGBM forecasting, conformal uncertainty bounds, doubly robust causal promotion lift (AIPW), and MinT hierarchical reconciliation into a containerized FastAPI microservice with MLflow tracking and Google Cloud deployment paths.

### 30-Second Recruiter Pitch
> **Problem**: Standard retail point forecasts fail to account for uncertainty, promotional selection bias, and inventory stockout costs.  
> **Approach**: Built DemandPulse, an end-to-end demand intelligence platform leveraging global LightGBM gradient boosting, conformal prediction bounds, doubly robust AIPW causal estimation, and MinT hierarchical forecast reconciliation.  
> **Technical Depth**: Developed a modular Python package with chronologically safe temporal features, 64 comprehensive pytest unit/integration tests, and mathematical coverage guarantees.  
> **Production Engineering**: Containerized with multi-stage Docker, served via FastAPI (sub-10ms latency), governed by MLflow model registry gates, and monitored for live PSI/KS data drift.  
> **Result**: Achieved a 53.6% WAPE reduction over baseline models, eliminated 49% promotional lift bias, and reduced simulated inventory costs by 61.9%.

---

## 12. License

This project is open-source software licensed under the [MIT License](LICENSE).
