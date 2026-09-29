def test_health_returns_200_and_model_readiness(client, fake_service):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"] == "DemandPulse"
    assert body["models_loaded"]["point"] is True
    assert fake_service.load_calls == 1


def test_swagger_docs_are_available(client):
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()


def test_model_info_returns_safe_metadata(client):
    response = client.get("/model/info")
    assert response.status_code == 200
    body = response.json()
    assert body["models"][0]["model_name"] == "demandpulse-point-forecast"
    serialized = str(body).lower()
    assert "model_dir" not in serialized
    assert "password" not in serialized


def test_health_is_liveness_even_when_models_are_not_ready(fake_service):
    from fastapi.testclient import TestClient

    from demandpulse.api.main import create_app

    fake_service.models_loaded = {"point": False, "probabilistic": False, "causal": False}
    fake_service.readiness_report = lambda: {
        "ready": False,
        "required_components": ["point", "probabilistic"],
        "models_loaded": fake_service.models_loaded,
        "missing_components": ["point", "probabilistic"],
        "reason": "required model artifacts are not loaded",
    }
    with TestClient(create_app(model_service=fake_service)) as client:
        health = client.get("/health")
        ready = client.get("/ready")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"
    assert ready.status_code == 503
    assert ready.json()["status"] == "not_ready"
