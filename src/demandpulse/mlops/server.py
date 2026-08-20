"""MLflow tracking-server launcher for a persistent Cloud Run deployment."""

from __future__ import annotations

import os


def build_mlflow_server_command() -> list[str]:
    """Build the MLflow server command from environment-only configuration."""
    backend = os.environ.get("MLFLOW_BACKEND_STORE_URI")
    artifacts = os.environ.get("MLFLOW_ARTIFACT_ROOT")
    if not backend:
        raise RuntimeError("MLFLOW_BACKEND_STORE_URI is required for production MLflow")
    if not artifacts:
        raise RuntimeError("MLFLOW_ARTIFACT_ROOT is required for production MLflow")
    port = os.environ.get("PORT", "5000")
    allowed_hosts = os.environ.get("MLFLOW_ALLOWED_HOSTS", "*.run.app,localhost:*")
    return [
        "mlflow",
        "server",
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
        "--backend-store-uri",
        backend,
        "--artifacts-destination",
        artifacts,
        "--serve-artifacts",
        "--allowed-hosts",
        allowed_hosts,
    ]


def main() -> None:
    command = build_mlflow_server_command()
    os.execvp(command[0], command)


if __name__ == "__main__":
    main()
