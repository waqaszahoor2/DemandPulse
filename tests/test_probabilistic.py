import numpy as np
import pandas as pd

from demandpulse.forecasting.probabilistic import (
    apply_conformal_adjustment,
    calculate_conformal_adjustment,
    repair_quantile_crossing,
)


def test_quantile_crossing_repair():
    frame = pd.DataFrame({"p10": [5.0, 1.0], "p50": [3.0, 2.0], "p90": [4.0, 3.0]})
    fixed = repair_quantile_crossing(frame)
    assert np.all(fixed["p10"] <= fixed["p50"])
    assert np.all(fixed["p50"] <= fixed["p90"])


def test_conformal_adjustment_is_nonnegative_and_applies():
    qhat = calculate_conformal_adjustment([5, 10, 15], [4, 8, 13], [6, 9, 14], alpha=0.2)
    assert qhat >= 0
    lo, hi = apply_conformal_adjustment([1, 2], [3, 4], qhat)
    assert np.all(lo >= 0)
    assert np.all(hi >= np.array([3, 4]))
