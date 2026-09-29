def test_point_forecast_valid_request(client, valid_forecast_payload):
    response = client.post("/forecast", json=valid_forecast_payload)
    assert response.status_code == 200
    body = response.json()
    assert body["prediction"] >= 0
    assert body["model_version"] == "point-test-v1"
    assert body["store_id"] == 10


def test_point_forecast_rejects_negative_historical_demand(client, valid_forecast_payload):
    payload = dict(valid_forecast_payload)
    payload["lag_1"] = -1
    response = client.post("/forecast", json=payload)
    assert response.status_code == 422


def test_point_forecast_rejects_missing_feature(client, valid_forecast_payload):
    payload = dict(valid_forecast_payload)
    payload.pop("lag_7")
    response = client.post("/forecast", json=payload)
    assert response.status_code == 422


def test_point_forecast_rejects_target_leakage_field(client, valid_forecast_payload):
    payload = dict(valid_forecast_payload)
    payload["sale_amount"] = 999
    response = client.post("/forecast", json=payload)
    assert response.status_code == 422


def test_promotion_effect_returns_observational_warning(client):
    payload = {
        "store_id": 10,
        "product_id": 100,
        "city_id": 1,
        "management_group_id": 2,
        "first_category_id": 3,
        "second_category_id": 4,
        "third_category_id": 5,
        "date": "2026-08-21",
        "lag_1": 10.0,
        "lag_7": 11.0,
        "lag_14": 10.0,
        "lag_28": 9.0,
        "rolling_mean_7": 10.0,
        "rolling_mean_28": 9.0,
        "rolling_std_7": 2.0,
        "rolling_std_28": 2.5,
        "stockout_lag_1": 0.0,
        "stockout_lag_7": 1.0,
        "holiday_flag": 0,
    }
    response = client.post("/promotion-effect", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["effect_type"] == "CATE"
    assert "observational" in body["warning"].lower()


def test_model_service_loads_real_local_point_model_and_predicts(tmp_path, valid_forecast_payload):
    import numpy as np
    import pandas as pd

    from demandpulse.api.model_service import ModelService
    from demandpulse.config import DemandPulseConfig
    from demandpulse.forecasting.point_model import save_point_model, train_point_model

    n = 60
    frame = pd.DataFrame(
        {
            "lag_1": np.linspace(1, 20, n),
            "day_of_week": np.arange(n) % 7,
        }
    )
    frame["sale_amount"] = 0.9 * frame["lag_1"] + 0.2 * frame["day_of_week"]
    model, metadata = train_point_model(
        frame,
        feature_columns=["lag_1", "day_of_week"],
        categorical_features=[],
        params={"n_estimators": 20, "num_leaves": 7, "min_child_samples": 5},
    )
    config = DemandPulseConfig(project_root=tmp_path)
    _, metadata_path = save_point_model(model, config.point_model_path, metadata)
    metadata_path.unlink()  # research Notebook 01 may only persist the native booster

    service = ModelService(config)
    service.load_models()
    result = service.predict_point_forecast(valid_forecast_payload)
    assert service.models_loaded["point"] is True
    assert result["prediction"] >= 0
    assert result["model_version"] != "unavailable"
