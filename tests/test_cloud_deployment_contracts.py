from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_deploy_workflow_uses_wif_immutable_image_and_staging_gate():
    workflow = (ROOT / ".github" / "workflows" / "deploy.yml").read_text(encoding="utf-8")
    assert "google-github-actions/auth@v3" in workflow
    assert "id-token: write" in workflow
    assert "${GITHUB_SHA}" in workflow
    assert "Artifact Registry" in workflow
    assert "environment: staging" in workflow
    assert "environment: production" in workflow
    assert "scripts/smoke_test.py" in workflow
    assert "scripts/load_test.py" in workflow
    assert "/forecast" in workflow
    assert "update-traffic" in workflow
    assert "demandpulse-api:latest" not in workflow.lower()


def test_cloud_run_probes_separate_readiness_and_liveness():
    workflow = (ROOT / ".github" / "workflows" / "deploy.yml").read_text(encoding="utf-8")
    assert "startup-probe \"httpGet.path=/ready" in workflow
    assert "liveness-probe \"httpGet.path=/health" in workflow


def test_production_docs_exist():
    for name in ["deployment.md", "monitoring.md", "rollback.md", "runbook.md"]:
        path = ROOT / "deployment" / name
        assert path.is_file()
        assert path.stat().st_size > 500


def test_env_example_contains_production_knobs_without_values():
    env = (ROOT / ".env.example").read_text(encoding="utf-8")
    keys = {line.split("=", 1)[0] for line in env.splitlines() if line.strip()}
    for key in {
        "APP_ENV",
        "LOG_LEVEL",
        "MODEL_BUNDLE_URI",
        "PORT",
        "REQUEST_TIMEOUT_SECONDS",
        "MAX_REQUEST_BYTES",
        "METRICS_ENABLED",
    }:
        assert key in keys
    assert all(line.endswith("=") for line in env.splitlines() if line.strip())
