"""Inventory calculations driven by probabilistic forecasts."""

from __future__ import annotations

import numpy as np
from scipy.stats import norm


def _validate_quantiles(p10: float, p50: float, p90: float) -> None:
    values = np.asarray([p10, p50, p90], dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Forecast quantiles must be finite")
    if not p10 <= p50 <= p90:
        raise ValueError("Forecast quantiles must satisfy P10 <= P50 <= P90")


def calculate_safety_stock(p50: float, p90: float) -> float:
    """Use the modeled upper-quantile premium above P50 as safety stock."""
    if not np.isfinite([p50, p90]).all() or p90 < p50:
        raise ValueError("Require finite p50 <= p90")
    return float(max(p90 - p50, 0.0))


def calculate_reorder_point(
    expected_demand: float,
    safety_stock: float,
    *,
    lead_time_days: float = 1.0,
) -> float:
    """Demand during lead time plus safety stock."""
    if expected_demand < 0 or safety_stock < 0 or lead_time_days <= 0:
        raise ValueError("Demand/safety stock must be non-negative and lead time positive")
    return float(expected_demand * lead_time_days + safety_stock)


def _normal_from_quantiles(p10: float, p50: float, p90: float) -> tuple[float, float]:
    _validate_quantiles(p10, p50, p90)
    z = norm.ppf(0.90)
    sigma = max((p90 - p10) / (2.0 * z), 1e-9)
    return float(p50), float(sigma)


def calculate_stockout_probability(
    order_quantity: float,
    p10: float,
    p50: float,
    p90: float,
) -> float:
    """Approximate P(demand > order quantity) from P10/P50/P90 via a normal fit."""
    if order_quantity < 0:
        raise ValueError("order_quantity must be non-negative")
    mean, sigma = _normal_from_quantiles(p10, p50, p90)
    return float(1.0 - norm.cdf(order_quantity, loc=mean, scale=sigma))


def _interpolate_quantile(p10: float, p50: float, p90: float, probability: float) -> float:
    _validate_quantiles(p10, p50, p90)
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be in [0, 1]")
    if probability <= 0.10:
        return max(0.0, p10 * probability / 0.10)
    if probability <= 0.50:
        weight = (probability - 0.10) / 0.40
        return p10 + weight * (p50 - p10)
    if probability <= 0.90:
        weight = (probability - 0.50) / 0.40
        return p50 + weight * (p90 - p50)
    # Conservative linear continuation above P90 when the requested service target is higher.
    slope = (p90 - p50) / 0.40
    return max(0.0, p90 + slope * (probability - 0.90))


def recommend_inventory(
    p10: float,
    p50: float,
    p90: float,
    *,
    service_level: float,
    holding_cost: float,
    stockout_cost: float,
) -> dict[str, float]:
    """Recommend a quantity from service and underage/overage risk without hard-coded costs."""
    _validate_quantiles(p10, p50, p90)
    if not 0.0 < service_level < 1.0:
        raise ValueError("service_level must be in (0, 1)")
    if holding_cost < 0 or stockout_cost < 0 or holding_cost + stockout_cost <= 0:
        raise ValueError("holding_cost and stockout_cost must be non-negative with positive total")
    critical_fractile = stockout_cost / (stockout_cost + holding_cost)
    decision_probability = max(service_level, critical_fractile)
    quantity = float(max(_interpolate_quantile(p10, p50, p90, decision_probability), 0.0))
    return {
        "recommended_quantity": quantity,
        "critical_fractile": float(critical_fractile),
        "decision_probability": float(decision_probability),
        "safety_stock": calculate_safety_stock(p50, p90),
        "stockout_probability": calculate_stockout_probability(quantity, p10, p50, p90),
    }
