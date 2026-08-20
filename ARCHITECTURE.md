# DemandPulse Architecture & System Design

DemandPulse is built as a production-grade retail demand intelligence platform that separates data validation, feature engineering, statistical forecasting, causal effect estimation, inventory optimization, model tracking, API serving, and production monitoring into modular, testable components.

---

## 1. System Architecture Diagram

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

---

## 2. Component Purpose

| Component | Sub-Package | Key Responsibilities |
| :--- | :--- | :--- |
| **Data Ingestion & Validation** | `demandpulse.data` | Deterministic SHA-256 series sampling from `FreshRetailNet-50K`, strict schema validation, missing value detection, duplicate timestamp rejection, chronological train/val splits. |
| **Feature Engineering** | `demandpulse.features` | Leakage-safe lag creation (lag 1, 7, 14, etc.), rolling window statistics (rolling mean, rolling std), calendar feature generation (day of week, month, quarter, is_weekend). |
| **Point Forecasting** | `demandpulse.forecasting.point_model` | Global LightGBM gradient boosting model lifecycle, categorical feature handling, native model serialization, non-negative clipping, baseline models (Seasonal Naive, Moving Average). |
| **Probabilistic Forecasting** | `demandpulse.forecasting.probabilistic` | Horizon-specific quantile LightGBM models (P10, P50, P90), quantile crossing repair, conformal prediction calibration intervals. |
| **Hierarchical Forecasting** | `demandpulse.forecasting.hierarchical` | Multi-level aggregation (`Company → City → Store → Store-Category → Product`), sparse summing matrix construction, Bottom-Up, Top-Down, Middle-Out, and MinT-shrinkage reconciliation. |
| **Causal Promotion Engine** | `demandpulse.causal` | Propensity score modeling (Logistic/GBDT), Inverse Propensity Weighting (IPW), Doubly Robust Augmented IPW (AIPW), Average Treatment Effect (ATE), Treatment Effect on Treated (ATT), Conditional ATE (CATE). |
| **Inventory Optimization** | `demandpulse.optimization` | Translating forecast uncertainty (P10/P50/P90) into operational inventory decisions (Safety Stock, Reorder Point, Stockout Risk, Service Level, Cost-Optimal Order Quantities). |
| **API Serving Layer** | `demandpulse.api` | Thin, high-performance FastAPI server with lifespan model loading, input validation, strict leakage prevention schema, Uvicorn ASGI server, structured JSON telemetry. |
| **MLOps & Tracking** | `demandpulse.mlops` | MLflow experiment tracking, artifact persistence, model registry management, candidate vs. champion promotion gates, rollback aliasing, immutable model bundle hydration. |
| **Container & Cloud** | `Dockerfile`, `deployment/` | Multi-stage Docker build, non-root user execution, Google Cloud Run autoscaling deployment, Workload Identity Federation authentication, health & readiness probes. |
| **Production Monitoring** | `demandpulse.monitoring` | Population Stability Index (PSI), 2-sample Kolmogorov-Smirnov (KS) tests, feature/target drift detection, actual-outcome joining, performance degradation tracking, GREEN/YELLOW/RED alerting logic, persistent retraining policy. |

---

## 3. Data Flow

1. **Ingestion**: Raw records stream from Hugging Face (`Dingdong-Inc/FreshRetailNet-50K`).
2. **Validation**: Rows pass schema verification (`store_id`, `product_id`, `date`, `sale_amount`, `promotion`, etc.). Complete time series are deterministically selected using a SHA-256 hash of `(store_id, product_id)`.
3. **Feature Generation**: Lags and rolling features are computed strictly using historical observations $t-k$ ($k \ge 1$), preventing target leakage.
4. **Model Input**: Processed feature vectors enter forecasting, causal, and reconciliation pipelines.
5. **Output Materialization**: Point forecasts, quantile bounds, reconciled totals, treatment effect estimates, and inventory recommendations are served via REST API and logged as structured JSON prediction events.

---

## 4. Training Flow

```text
Historical Data → Chronological Split → Feature Engineering → Baseline Models (Naive/MA)
                                                             ↓
                                              Global LightGBM Point Model
                                                             ↓
                                            Quantile Models (P10/P50/P90)
                                                             ↓
                                             Conformal Interval Calibration
                                                             ↓
                                            Hierarchical MinT Reconciliation
                                                             ↓
                                              Causal Nuisance Models (Propensity + Outcome)
                                                             ↓
                                          MLflow Logging & Champion Bundle Artifact Creation
```

---

## 5. Inference Flow

```text
HTTP Request → FastAPI Validation (Schema check + Leakage filter)
                     ↓
               Model Service
                     ↓
┌────────────────────┼────────────────────┐
↓                    ↓                    ↓
Point Forecast    Probabilistic Forecast  Causal / Inventory Engine
(LightGBM Champion) (P10/P50/P90 + Conformal) (Safety Stock & Order Qty)
└────────────────────┬────────────────────┘
                     ↓
         JSON Response Generation (X-Request-ID Attached)
                     ↓
         Structured Prediction Log Emission
```

---

## 6. Monitoring & Retraining Flow

```text
Live Prediction Logs + Delayed Actual Outcomes
                     ↓
             Outcome Matcher Join
                     ↓
 ┌───────────────────┴───────────────────┐
 ↓                                       ↓
Data Drift Diagnostics                  Forecast Performance Metrics
(PSI, KS Test, Null Rate)               (WAPE, MAE, Bias, Pinball, Coverage)
 └───────────────────┬───────────────────┘
                     ↓
        Configurable Alerting Engine
     (GREEN: Normal | YELLOW: Warning | RED: Alert)
                     ↓
        Retraining Decision Engine
 (Triggers only if: Persistent Degradation + Sufficient New Labels + Clean Data)
                     ↓
     Candidate Model Retraining & MLflow Promotion Gate
```
