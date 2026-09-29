from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dockerfile_uses_non_root_production_server_and_healthcheck():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "FROM python:3.11.9-slim-bookworm" in dockerfile
    assert "USER demandpulse" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "uvicorn demandpulse.api.main:app" in dockerfile
    assert "--reload" not in dockerfile
    assert "BUILD_DEPENDENCIES.txt" in dockerfile
    assert "BUILD_INFO.txt" in dockerfile


def test_dockerignore_excludes_secret_and_research_only_content_but_not_models():
    lines = {line.strip() for line in (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()}
    assert ".env" in lines
    assert "notebooks/" in lines
    assert "reports/" in lines
    assert "mlruns/" in lines
    assert "models/" not in lines


def test_compose_uses_service_dns_for_mlflow_and_persistent_volumes():
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "MLFLOW_TRACKING_URI: http://mlflow:5000" in compose
    assert "mlflow-data:/mlflow" in compose
    assert "demandpulse-models:/app/models" in compose
    assert "--artifacts-destination /mlflow/artifacts" in compose
    assert "--allowed-hosts" in compose
    assert "mlflow:5000" in compose


def test_env_example_contains_no_secret_values():
    content = (ROOT / ".env.example").read_text(encoding="utf-8")
    for line in content.splitlines():
        if not line.strip():
            continue
        key, value = line.split("=", 1)
        assert key.strip()
        assert value == ""
