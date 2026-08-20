# DemandPulse Interview Preparation & Technical Notes

This guide provides concise, senior-level responses to technical interview questions about the DemandPulse platform architecture, algorithms, and design choices.

---

## 1. Tell me about DemandPulse.
**DemandPulse** is an end-to-end, production-oriented retail demand intelligence system. Rather than treating demand planning as a single point-forecasting problem, it decouples expected demand, uncertainty quantification, causal promotion lift estimation, hierarchical accounting reconciliation, and cost-aware inventory optimization. It bridges research notebooks with production software using a modular Python package, FastAPI serving, MLflow tracking/registry, multi-stage Docker builds, GitHub Actions quality gates, and Google Cloud Run deployment architecture.

---

## 2. Why LightGBM?
Global LightGBM gradient boosted decision trees were selected over single-series ARIMA or complex DeepAR/Temporal Fusion Transformers because:
1. **Cross-Series Feature Sharing**: A single global model trains across all store-product time series simultaneously, learning shared seasonal and promotional patterns.
2. **Speed & Efficiency**: Histogram-based feature binning enables fast training and sub-10ms CPU inference.
3. **Categorical Handling**: Native support for categorical features (`store_id`, `product_id`, `city`, `category_id`).
4. **Quantile Loss Support**: Native `objective='quantile'` optimization for multi-quantile P10/P50/P90 forecasting without deep learning dependencies.

---

## 3. Why not a random train/test split?
Random train/test splits cause severe **temporal data leakage** in time-series problems. Future observations would bleed into lag features, rolling statistics, and target variables of past rows, yielding artificially high validation metrics that fail in production. DemandPulse enforces strict **chronological backtesting** with rolling-origin temporal folds ($T_{\text{train}} < T_{\text{val}} < T_{\text{test}}$), ensuring no future information is accessible during training.

---

## 4. What is WAPE?
**Weighted Absolute Percentage Error (WAPE)** measures aggregate forecast error relative to total demand:

$$\text{WAPE} = \frac{\sum |y_t - \hat{y}_t|}{\sum y_t}$$

Unlike MAPE (Mean Absolute Percentage Error), WAPE does not blow up or divide by zero on low-volume or zero-demand days, making it the industry standard metric for retail demand forecasting across diverse store-product SKUs.

---

## 5. What is probabilistic forecasting?
While point forecasting predicts a single expected scalar value ($\hat{y}$), **probabilistic forecasting** estimates the conditional distribution of future demand—typically via prediction intervals or quantiles (P10, P50, P90). P10 represents a conservative downside scenario (10% chance demand is lower), P50 is median demand, and P90 represents upside demand. This enables risk-aware inventory replenishment based on stockout costs and holding costs.

---

## 6. What is conformal prediction?
Quantile regression models can suffer from miscalibration or quantile crossing on unseen out-of-fold data. **Conformal prediction** uses historical residual errors from a calibration set to adjust raw quantile bounds:

$$\hat{q}_{\text{conformal}} = \hat{q}_{\alpha} \pm s_{1-\alpha}$$

This guarantees finite-sample coverage coverage (e.g., exactly 80% empirical coverage for P10–P90) without making strong parametric distribution assumptions (like Gaussianity).

---

## 7. What is AIPW?
**Augmented Inverse Propensity Weighting (AIPW)** is a doubly robust causal inference estimator. It combines a propensity score model $e(X) = P(T=1|X)$ with outcome regression models $\mu_1(X) = E[Y|X, T=1]$ and $\mu_0(X) = E[Y|X, T=0]$:

$$\hat{\tau}_{\text{AIPW}} = \frac{1}{N} \sum_{i=1}^N \left( \frac{T_i Y_i - (T_i - e(X_i))\mu_1(X_i)}{e(X_i)} - \frac{(1-T_i)Y_i + (T_i - e(X_i))\mu_0(X_i)}{1 - e(X_i)} \right)$$

It is **doubly robust** because the ATE estimate remains unbiased if *either* the propensity model OR the outcome model is correctly specified.

---

## 8. What is CATE?
**Conditional Average Treatment Effect (CATE)** estimates treatment heterogeneity across specific sub-populations or feature spaces $X$:

$$\tau(x) = E[Y(1) - Y(0) \mid X = x]$$

In DemandPulse, CATE determines which specific store-category-product combinations experience true incremental demand lift from a promotion versus products where promotions merely discount demand that would have occurred anyway.

---

## 9. What is forecast reconciliation?
Retail demand exists across nested structural hierarchies (`Company → City → Store → Store-Category → Product`). When forecasts are generated independently at each level, bottom-level predictions do not sum to top-level predictions (accounting incoherence). **Forecast reconciliation** projects incoherent base forecasts $\hat{y}$ using a linear summing matrix $S$ and error covariance weighting matrix $W$ via MinT (Minimum Trace):

$$\tilde{y} = S (S^T W^{-1} S)^{-1} S^T W^{-1} \hat{y}$$

This guarantees 100% accounting coherence while reducing overall forecast variance across all levels.

---

## 10. What was the hardest technical problem in DemandPulse?
Preventing subtle **data leakage** across multi-step forecasting, causal propensity estimation, and hierarchical reconciliation. For example:
- In causal propensity modeling, ensuring same-day sales and post-treatment stock statuses were explicitly excluded from propensity features to avoid conditioning on post-treatment colliders.
- In feature engineering, ensuring rolling windows were computed strictly using shift-based lag operators ($t-k, k \ge 1$) so future target values were never included in rolling means.

---

## 11. What would you improve next?
1. **Intermittent Demand Handlers**: Incorporating specialized Croston/SBA or Deep Renewal processes for extreme zero-inflated long-tail SKUs.
2. **Stockout Uncensoring**: Implementing Tobit regression or Kaplan-Meier survival curves to estimate unconstrained demand on out-of-stock days.
3. **Automated Feature Store**: Integrating Feast or Hopsworks to serve point-in-time correct lag features at scale.

---

## 12. How would this scale to a real retailer?
For a enterprise retailer managing 10M+ store-SKU time series:
- **Feature Engineering**: Migrate pandas lag generation to PySpark / Ray / BigQuery SQL for distributed processing.
- **Model Training**: Parallelize LightGBM training per category using Ray / Spark ML, or deploy distributed LightGBM on Kubernetes GPU/CPU clusters.
- **Serving Layer**: Deploy FastAPI on Cloud Run / EKS with horizontal pod autoscaling, backed by Redis for feature caching and Triton / ONNX Runtime for sub-millisecond C++ tree inference.
