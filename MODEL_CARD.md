# DemandPulse Model Card

## Model Overview

DemandPulse employs a suite of production machine learning and statistical models engineered for retail demand forecasting, probabilistic risk estimation, causal promotion analysis, and inventory optimization.

| Model Category | Primary Architecture | Key Hyperparameters / Methods | Serialization |
| :--- | :--- | :--- | :--- |
| **Point Forecast** | LightGBM Regressor (`LGBMRegressor`) | `n_estimators=300`, `learning_rate=0.05`, `num_leaves=31`, `objective='regression_l1'` | Native `.txt` + JSON metadata sidecar |
| **Probabilistic Forecast** | Multi-Quantile LightGBM Regressors | `objective='quantile'`, $\alpha \in \{0.10, 0.50, 0.90\}$, Conformal Calibration | Per-horizon quantile `.txt` bundles |
| **Causal Promotion Engine** | Logistic Propensity + LightGBM Outcome | Doubly Robust AIPW, IPW, Cross-Fitting | Joblib pickled pipeline + JSON config |
| **Hierarchical Reconciliation** | Sparse MinT Matrix Solver | Shrinkage Covariance Matrix ($W$), Bottom-Up, Top-Down | SciPy CSR Sparse Matrix + Python package |

---

## Intended Use

- **Primary Application**: Automated retail inventory replenishment, promotional planning, store-level safety stock calculation, and executive hierarchy aggregation.
- **Target Users**: Demand planners, supply chain analysts, inventory managers, automated ERP systems, and business intelligence teams.
- **Deployment Context**: Cloud containerized microservice (FastAPI + Docker + Google Cloud Run) with MLflow model registry governance.

---

## Training Data & Features

- **Source Dataset**: `Dingdong-Inc/FreshRetailNet-50K` (Hugging Face streaming dataset).
- **Sampling Scheme**: Deterministic complete-series selection using SHA-256 hash of `(store_id, product_id)`.
- **Target Variable**: `sale_amount` (daily product unit sales).
- **Treatment Variable**: `promotion` (binary indicator for active promotion/discount).
- **Feature Set**:
  - **Lags**: $t-1, t-7, t-14, t-21, t-28$ (strictly historical observations).
  - **Rolling Statistics**: 7-day and 14-day rolling mean, rolling standard deviation, rolling min/max.
  - **Calendar**: Day of week, month, quarter, day of year, weekend flag.
  - **Categoricals**: `store_id`, `product_id`, `city`, `category_id`.

---

## Validation Methodology

- **Evaluation Scheme**: Chronological backtesting with rolling-origin temporal splits.
- **Leakage Safeguards**:
  - Rejection of same-day target `sale_amount` or same-day stock status as predictors.
  - No future validation rows passed into training folds.
  - Temporal ordering strictly maintained ($T_{\text{train}} < T_{\text{val}} < T_{\text{test}}$).

---

## Evaluation Metrics

- **Point Forecast**: WAPE (Weighted Absolute Percentage Error), MAE, RMSE, Bias.
- **Probabilistic Forecast**: Pinball Loss, Empirical Coverage ($\% \in [P_{10}, P_{90}]$), Interval Width, Interval Score.
- **Causal Promotion Effect**: ATE (Average Treatment Effect), ATT (Effect on Treated), 95% Confidence Intervals via Sandwich Variance.
- **Hierarchical Consistency**: Coherence Error $\|y - S\tilde{y}\|_2$, Level-weighted WAPE.

---

## Limitations

1. **Normalized Target**: `sale_amount` represents normalized index demand rather than raw physical unit counts.
2. **Stockout Censoring**: Observed historical sales represent realized sales under available inventory, which may censor true unconstrained customer demand during out-of-stock periods.
3. **Quantile Coverage**: P10/P50/P90 form discrete interval bounds, not a full continuous probability density function.
4. **Observational Confounding**: Causal promotion estimates rely on unconfoundedness assumptions. Residual unmeasured promotional factors (e.g., endcap displays, email campaigns) may introduce estimation bias.

---

## Unsupported Uses

- Financial reporting or audited accounting statements without human review.
- High-frequency intra-day demand prediction (model is trained on daily aggregated series).
- Fully automated price elasticity optimization without experimental A/B testing.
- Extrapolation to novel product categories or international markets without historical retraining.

---

## Known Failure Modes

- **Cold-Start Products**: Newly introduced SKUs with $<14$ days of sales history lack required lag features and default to baseline category estimates.
- **Intermittent / Zero-Inflated Demand**: Slow-moving SKUs with high zero-frequency can lead to quantile crossing, handled automatically via monotonic adjustment.
- **Structural Demand Shocks**: Unprecedented macro shocks (e.g., pandemic disruptions) invalidate historical rolling averages until retraining occurs.

---

## Production Monitoring & Retraining

- **Drift Diagnostics**: Population Stability Index (PSI) and Kolmogorov-Smirnov (KS) tests monitored on input feature distributions.
- **Performance Monitoring**: Real-time evaluation of incoming actuals against stored predictions.
- **Retraining Trigger**: Automated alert escalation (GREEN $\rightarrow$ YELLOW $\rightarrow$ RED) requiring persistent performance degradation over $\ge 7$ consecutive days before triggering candidate model retraining.
