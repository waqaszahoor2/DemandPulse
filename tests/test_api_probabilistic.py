def test_probabilistic_forecast_quantiles_are_ordered(client, valid_forecast_payload):
    payload = dict(valid_forecast_payload)
    payload["horizon"] = 3
    response = client.post("/forecast/probabilistic", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["p10"] <= body["p50"] <= body["p90"]
    assert body["interval_lower"] <= body["interval_upper"]
    assert body["horizon"] == 3
    assert body["conformal_applied"] is True


def test_probabilistic_forecast_rejects_unsupported_horizon(client, valid_forecast_payload):
    payload = dict(valid_forecast_payload)
    payload["horizon"] = 8
    response = client.post("/forecast/probabilistic", json=payload)
    assert response.status_code == 422


def test_model_service_loads_real_quantile_artifacts_and_applies_conformal(tmp_path, valid_forecast_payload):
    import json

    import numpy as np
    import pandas as pd

    from demandpulse.api.model_service import ModelService
    from demandpulse.config import DemandPulseConfig
    from demandpulse.forecasting.probabilistic import train_quantile_model

    n = 80
    train = pd.DataFrame(
        {
            "lag_1": np.linspace(1, 20, n),
            "forecast_day_of_week": np.arange(n) % 7,
        }
    )
    train["target"] = train["lag_1"] + 0.3 * train["forecast_day_of_week"]
    config = DemandPulseConfig(project_root=tmp_path)
    config.quantile_models_dir.mkdir(parents=True, exist_ok=True)

    for quantile in (0.10, 0.50, 0.90):
        model, metadata = train_quantile_model(
            train,
            quantile,
            feature_columns=["lag_1", "forecast_day_of_week"],
            categorical_features=[],
            params={"n_estimators": 20, "num_leaves": 7, "min_child_samples": 5},
            config=config,
        )
        q_int = int(round(quantile * 100))
        path = config.quantile_models_dir / f"h01_q{q_int:02d}.txt"
        model.booster_.save_model(str(path))
        # Research Notebook 02 saves native boosters; sidecars are intentionally omitted here.
    (config.quantile_models_dir / "conformal_adjustments.json").write_text(
        json.dumps({"1": {"q_hat": 1.0}}), encoding="utf-8"
    )

    service = ModelService(config)
    service.load_models()
    payload = dict(valid_forecast_payload)
    payload["horizon"] = 1
    result = service.predict_probabilistic_forecast(payload)
    assert service.models_loaded["probabilistic"] is True
    assert 0 <= result["p10"] <= result["p50"] <= result["p90"]
    assert result["interval_lower"] <= result["p10"]
    assert result["interval_upper"] >= result["p90"]
    assert result["conformal_applied"] is True
