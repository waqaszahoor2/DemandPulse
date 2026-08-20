import numpy as np

from demandpulse.optimization.inventory import (
    calculate_reorder_point,
    calculate_safety_stock,
    calculate_stockout_probability,
    recommend_inventory,
)


def test_inventory_functions_are_nonnegative():
    safety = calculate_safety_stock(10, 15)
    assert safety == 5
    assert calculate_reorder_point(10, safety, lead_time_days=2) == 25
    decision = recommend_inventory(5, 10, 15, service_level=0.9, holding_cost=1, stockout_cost=4)
    assert decision["recommended_quantity"] >= 0
    assert 0 <= decision["stockout_probability"] <= 1


def test_more_inventory_reduces_stockout_probability():
    low = calculate_stockout_probability(8, 5, 10, 15)
    high = calculate_stockout_probability(16, 5, 10, 15)
    assert high < low
