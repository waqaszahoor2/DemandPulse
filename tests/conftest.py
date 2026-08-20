from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from demandpulse.api.main import create_app


class FakeModelService:
    def __init__(self) -> None:
        self.load_calls = 0
        self.models_loaded = {"point": True, "probabilistic": True, "causal": True}

    @property
    def serving_model_version(self) -> str:
        return "point-test-v1"

    def readiness_report(self) -> dict[str, object]:
        return {
            "ready": True,
            "required_components": ["point", "probabilistic"],
            "models_loaded": self.models_loaded,
            "missing_components": [],
            "reason": None,
        }

    def load_models(self) -> None:
        self.load_calls += 1

    def predict_point_forecast(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"prediction": 12.5, "model_version": "point-test-v1"}

    def predict_probabilistic_forecast(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "p10": 8.0,
            "p50": 12.0,
            "p90": 18.0,
            "interval_lower": 6.5,
            "interval_upper": 20.0,
            "horizon": int(payload["horizon"]),
            "model_version": "quantile-test-v1",
            "conformal_applied": True,
        }

    def predict_promotion_effect(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "estimated_treatment_effect": 1.25,
            "effect_type": "CATE",
            "ci_lower": 0.2,
            "ci_upper": 2.1,
            "model_version": "causal-test-v1",
            "warning": "Observational causal estimate subject to assumptions and residual confounding.",
        }

    def recommend_inventory(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "recommended_order_quantity": 9.0,
            "recommended_inventory_position": 19.0,
            "reorder_point": 20.0,
            "safety_stock": 6.0,
            "stockout_risk": 0.08,
            "assumptions": ["Test decision assumptions."],
        }

    def model_info(self) -> list[dict[str, Any]]:
        return [
            {
                "model_name": "demandpulse-point-forecast",
                "model_type": "LightGBM point forecast",
                "version": "point-test-v1",
                "training_date": "2026-08-20T00:00:00+00:00",
                "supported_forecast_horizon": 7,
                "metrics": {"WAPE": 0.2},
                "status": "champion",
            }
        ]


@pytest.fixture
def fake_service() -> FakeModelService:
    return FakeModelService()


@pytest.fixture
def client(fake_service: FakeModelService):
    app = create_app(model_service=fake_service)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def valid_forecast_payload() -> dict[str, Any]:
    return {
        "store_id": 10,
        "product_id": 100,
        "city_id": 1,
        "management_group_id": 2,
        "first_category_id": 3,
        "second_category_id": 4,
        "third_category_id": 5,
        "forecast_date": "2026-08-21",
        "lag_1": 10.0,
        "lag_2": 9.0,
        "lag_3": 8.0,
        "lag_7": 11.0,
        "lag_14": 10.0,
        "lag_28": 9.0,
        "rolling_mean_7": 10.0,
        "rolling_mean_14": 9.5,
        "rolling_mean_28": 9.0,
        "rolling_std_7": 2.0,
        "rolling_std_14": 2.2,
        "rolling_std_28": 2.5,
        "rolling_min_7": 6.0,
        "rolling_max_7": 14.0,
        "stockout_lag_1": 0.0,
        "stockout_lag_7": 1.0,
        "discount": 0.9,
        "holiday_flag": 0,
        "activity_flag": 1,
    }
