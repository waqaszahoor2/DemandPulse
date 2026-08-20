from __future__ import annotations

import pytest

from demandpulse.mlops.server import build_mlflow_server_command


def test_mlflow_cloud_server_requires_persistent_backends(monkeypatch):
    monkeypatch.delenv("MLFLOW_BACKEND_STORE_URI", raising=False)
    monkeypatch.delenv("MLFLOW_ARTIFACT_ROOT", raising=False)
    with pytest.raises(RuntimeError, match="BACKEND"):
        build_mlflow_server_command()


def test_mlflow_cloud_server_uses_env_and_cloud_run_port(monkeypatch):
    monkeypatch.setenv("MLFLOW_BACKEND_STORE_URI", "postgresql+psycopg2://example")
    monkeypatch.setenv("MLFLOW_ARTIFACT_ROOT", "gs://bucket/mlflow")
    monkeypatch.setenv("PORT", "5000")
    command = build_mlflow_server_command()
    assert command[0:2] == ["mlflow", "server"]
    assert "postgresql+psycopg2://example" in command
    assert "gs://bucket/mlflow" in command
    assert command[command.index("--port") + 1] == "5000"
    assert "--allowed-hosts" in command
