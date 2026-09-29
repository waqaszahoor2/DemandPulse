from __future__ import annotations

import numpy as np
import pandas as pd

from demandpulse.evaluation.backtesting import create_rolling_folds, run_backtest
from demandpulse.features.lag_features import add_lag_features
from demandpulse.forecasting.point_model import train_point_model


def test_current_target_cannot_change_its_own_rolling_features():
    frame = pd.DataFrame(
        {
            "store_id": [1] * 9,
            "product_id": [10] * 9,
            "dt": pd.date_range("2026-01-01", periods=9),
            "sale_amount": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0],
        }
    )
    original = add_lag_features(frame, stockout_col="missing_stock_column")
    changed = frame.copy()
    changed.loc[7, "sale_amount"] = 1_000_000.0
    changed_features = add_lag_features(changed, stockout_col="missing_stock_column")

    assert original.loc[7, "rolling_mean_7"] == changed_features.loc[7, "rolling_mean_7"]
    assert original.loc[7, "lag_1"] == changed_features.loc[7, "lag_1"]


def test_backtest_never_passes_future_validation_rows_into_training():
    frame = pd.DataFrame(
        {
            "dt": pd.date_range("2026-01-01", periods=30),
            "sale_amount": np.arange(30, dtype=float),
        }
    )
    folds = create_rolling_folds(frame["dt"], forecast_horizon=3, n_folds=3)

    def fit_predict(train: pd.DataFrame, valid: pd.DataFrame, fold):
        assert train["dt"].max() <= fold.train_end
        assert train["dt"].max() < valid["dt"].min()
        assert not train["dt"].isin(valid["dt"]).any()
        return np.zeros(len(valid), dtype=float)

    result = run_backtest(frame, folds, fit_predict)
    assert len(result) == 9


def test_training_rejects_same_day_target_and_stock_features():
    frame = pd.DataFrame(
        {
            "sale_amount": [1.0, 2.0, 3.0, 4.0],
            "stock_hour6_22_cnt": [0, 0, 1, 0],
        }
    )
    try:
        train_point_model(frame, feature_columns=["stock_hour6_22_cnt"], categorical_features=[])
    except ValueError as exc:
        assert "leakage" in str(exc).lower()
    else:
        raise AssertionError("same-day stock feature must be rejected")
