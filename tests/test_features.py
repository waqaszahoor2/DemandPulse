import numpy as np
import pandas as pd

from demandpulse.features.lag_features import add_lag_features
from demandpulse.features.time_features import add_time_features


def test_lags_and_rolling_are_leakage_safe():
    frame = pd.DataFrame({
        "store_id": [1] * 9,
        "product_id": [1] * 9,
        "dt": pd.date_range("2026-01-01", periods=9, freq="D"),
        "sale_amount": [1, 2, 3, 4, 5, 6, 7, 8, 999],
        "stock_hour6_22_cnt": [0] * 9,
    })
    out = add_lag_features(frame, lags=(1, 7), rolling_windows=(7,))
    assert out.loc[8, "lag_1"] == 8
    assert out.loc[8, "lag_7"] == 2
    assert np.isclose(out.loc[8, "rolling_mean_7"], np.mean([2, 3, 4, 5, 6, 7, 8]))
    assert out.loc[8, "rolling_max_7"] == 8
    assert out.loc[8, "rolling_max_7"] != 999


def test_time_features():
    frame = pd.DataFrame({"dt": pd.to_datetime(["2026-01-03"]), "holiday_flag": [1]})
    out = add_time_features(frame)
    assert out.loc[0, "is_weekend"] == 1
    assert out.loc[0, "is_holiday"] == 1
