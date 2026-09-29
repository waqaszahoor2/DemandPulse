import numpy as np
import pandas as pd

from demandpulse.evaluation.backtesting import create_rolling_folds
from demandpulse.forecasting.baselines import moving_average_forecast, seasonal_naive_forecast
from demandpulse.forecasting.hierarchical import bottom_up_reconciliation, build_summing_matrix
from demandpulse.forecasting.point_model import predict_point, train_point_model


class NegativeModel:
    def predict(self, X):
        return np.full(len(X), -3.0)


def test_negative_point_forecasts_are_clipped():
    frame = pd.DataFrame({"x": [1, 2]})
    metadata = {"feature_columns": ["x"], "category_levels": {}}
    prediction = predict_point(NegativeModel(), frame, metadata)
    assert np.all(prediction == 0.0)


def test_baselines_use_history_only():
    frame = pd.DataFrame(
        {
            "store_id": [1] * 8,
            "product_id": [1] * 8,
            "dt": pd.date_range("2026-01-01", periods=8),
            "sale_amount": np.arange(1, 9, dtype=float),
        }
    )
    seasonal = seasonal_naive_forecast(frame)
    assert seasonal.iloc[7] == 1.0
    ma = moving_average_forecast(frame, window=3)
    assert ma.iloc[3] == 2.0


def test_chronological_folds_have_no_overlap():
    dates = pd.date_range("2026-01-01", periods=30)
    folds = create_rolling_folds(dates, forecast_horizon=3, n_folds=3)
    assert all(f.train_end < f.validation_start for f in folds)
    assert folds[0].validation_end < folds[1].validation_start


def test_small_lightgbm_training_roundtrip_prediction():
    n = 80
    frame = pd.DataFrame(
        {
            "lag_1": np.linspace(1, 10, n),
            "day_of_week": np.arange(n) % 7,
            "store_id": np.where(np.arange(n) % 2 == 0, 1, 2),
            "product_id": np.where(np.arange(n) % 3 == 0, 10, 11),
        }
    )
    frame["sale_amount"] = 0.8 * frame["lag_1"] + 0.1 * frame["day_of_week"]
    model, metadata = train_point_model(
        frame,
        feature_columns=["lag_1", "day_of_week", "store_id", "product_id"],
        categorical_features=["store_id", "product_id"],
        params={"n_estimators": 20, "num_leaves": 7, "min_child_samples": 5},
    )
    pred = predict_point(model, frame.head(5), metadata)
    assert len(pred) == 5
    assert np.all(pred >= 0)


def test_bottom_up_uses_correct_product_mapping_order():
    mapping = pd.DataFrame(
        {
            "city_id": [1, 1],
            "store_id": [10, 10],
            "third_category_id": [5, 5],
            "product_id": [200, 100],  # deliberately non-sorted input order
        }
    )
    hierarchy = build_summing_matrix(mapping)
    base = np.zeros(len(hierarchy.nodes), dtype=float)
    node_index = dict(zip(hierarchy.nodes["node_id"], hierarchy.nodes["row_idx"]))
    base[node_index["Product:10:200"]] = 2.0
    base[node_index["Product:10:100"]] = 7.0
    reconciled = bottom_up_reconciliation(base, hierarchy)
    assert reconciled[node_index["Company"]] == 9.0
    assert reconciled[node_index["Product:10:200"]] == 2.0
    assert reconciled[node_index["Product:10:100"]] == 7.0
