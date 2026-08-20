"""Monte Carlo inventory scenario simulation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd
from scipy.stats import norm

from demandpulse.optimization.inventory import recommend_inventory


def _demand_draws(
    p10: float,
    p50: float,
    p90: float,
    n_draws: int,
    rng: np.random.Generator,
    *,
    demand_multiplier: float = 1.0,
    uncertainty_multiplier: float = 1.0,
    uplift: float = 0.0,
) -> np.ndarray:
    if n_draws <= 0:
        raise ValueError("n_draws must be positive")
    z = norm.ppf(0.90)
    sigma = max((p90 - p10) / (2.0 * z), 1e-9) * uncertainty_multiplier
    mean = p50 * demand_multiplier + uplift
    return np.maximum(rng.normal(mean, sigma, n_draws), 0.0)


def simulate_inventory_policy(
    demand: Sequence[float],
    order_quantity: float,
    *,
    unit_cost: float,
    selling_price: float,
    holding_cost: float,
    stockout_cost: float,
    waste_cost: float = 0.0,
    ordering_cost: float = 0.0,
    waste_fraction: float = 0.0,
) -> dict[str, float]:
    """Evaluate one fixed order quantity over simulated demand draws."""
    if any(value < 0 for value in [order_quantity, unit_cost, selling_price, holding_cost, stockout_cost, waste_cost, ordering_cost]):
        raise ValueError("Costs, prices, and order quantity must be non-negative")
    if not 0.0 <= waste_fraction <= 1.0:
        raise ValueError("waste_fraction must be in [0, 1]")
    y = np.asarray(demand, dtype=float)
    if np.any(y < 0) or not np.isfinite(y).all():
        raise ValueError("Demand draws must be finite and non-negative")
    q = float(order_quantity)
    fulfilled = np.minimum(y, q)
    shortage = np.maximum(y - q, 0.0)
    leftover = np.maximum(q - y, 0.0)
    waste = leftover * waste_fraction
    total_cost = (
        q * unit_cost
        + leftover * holding_cost
        + shortage * stockout_cost
        + waste * waste_cost
        + ordering_cost
    )
    revenue = fulfilled * selling_price
    profit = revenue - total_cost
    demand_sum = y.sum()
    return {
        "expected_cost": float(total_cost.mean()),
        "stockout_rate": float(np.mean(shortage > 0)),
        "service_level": float(fulfilled.sum() / demand_sum) if demand_sum > 0 else np.nan,
        "excess_inventory": float(leftover.mean()),
        "waste": float(waste.mean()),
        "simulated_profit": float(profit.mean()),
    }


def run_scenarios(
    forecasts: pd.DataFrame,
    *,
    cost_config: Mapping[str, float],
    p10_col: str = "p10",
    p50_col: str = "p50",
    p90_col: str = "p90",
    n_draws: int = 1_000,
    random_state: int = 42,
    promotion_uplift: float = 0.0,
) -> pd.DataFrame:
    """Run normal, promotion, high-demand, uncertain, stockout-risk, and high-holding-cost scenarios."""
    required = {p10_col, p50_col, p90_col}
    missing = sorted(required - set(forecasts.columns))
    if missing:
        raise KeyError(f"Forecast frame is missing: {missing}")
    required_costs = {"unit_cost", "selling_price", "holding_cost", "stockout_cost", "service_level"}
    missing_costs = sorted(required_costs - set(cost_config))
    if missing_costs:
        raise KeyError(f"cost_config is missing: {missing_costs}")

    scenarios = {
        "normal_demand": {"demand_multiplier": 1.0, "uncertainty_multiplier": 1.0, "uplift": 0.0},
        "promotion_demand": {"demand_multiplier": 1.0, "uncertainty_multiplier": 1.0, "uplift": promotion_uplift},
        "high_demand": {"demand_multiplier": 1.20, "uncertainty_multiplier": 1.0, "uplift": 0.0},
        "high_uncertainty": {"demand_multiplier": 1.0, "uncertainty_multiplier": 1.50, "uplift": 0.0},
        "stockout_risk": {"demand_multiplier": 1.15, "uncertainty_multiplier": 1.25, "uplift": 0.0},
        "high_holding_cost": {"demand_multiplier": 1.0, "uncertainty_multiplier": 1.0, "uplift": 0.0},
    }
    rng = np.random.default_rng(random_state)
    rows: list[dict[str, float | str]] = []
    for scenario, modifiers in scenarios.items():
        scenario_cost = dict(cost_config)
        if scenario == "high_holding_cost":
            scenario_cost["holding_cost"] = 2.0 * float(cost_config["holding_cost"])
        metrics_accum: list[dict[str, float]] = []
        for row in forecasts.itertuples(index=False):
            p10 = float(getattr(row, p10_col))
            p50 = float(getattr(row, p50_col))
            p90 = float(getattr(row, p90_col))
            decision = recommend_inventory(
                p10,
                p50,
                p90,
                service_level=float(scenario_cost["service_level"]),
                holding_cost=float(scenario_cost["holding_cost"]),
                stockout_cost=float(scenario_cost["stockout_cost"]),
            )
            draws = _demand_draws(p10, p50, p90, n_draws, rng, **modifiers)
            metrics_accum.append(
                simulate_inventory_policy(
                    draws,
                    decision["recommended_quantity"],
                    unit_cost=float(scenario_cost["unit_cost"]),
                    selling_price=float(scenario_cost["selling_price"]),
                    holding_cost=float(scenario_cost["holding_cost"]),
                    stockout_cost=float(scenario_cost["stockout_cost"]),
                    waste_cost=float(scenario_cost.get("waste_cost", 0.0)),
                    ordering_cost=float(scenario_cost.get("ordering_cost", 0.0)),
                    waste_fraction=float(scenario_cost.get("waste_fraction", 0.0)),
                )
            )
        result = pd.DataFrame(metrics_accum)
        aggregate = result.mean(numeric_only=True).to_dict()
        aggregate["scenario"] = scenario
        aggregate["rows"] = float(len(result))
        rows.append(aggregate)
    return pd.DataFrame(rows)
