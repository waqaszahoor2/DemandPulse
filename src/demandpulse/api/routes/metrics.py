"""Internal low-cardinality application metrics endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(tags=["monitoring"])


@router.get("/internal/metrics", include_in_schema=False)
def internal_metrics(request: Request) -> dict:
    """Return bounded aggregate service metrics; no payloads or secrets are exposed."""
    if not getattr(request.app.state, "metrics_enabled", False):
        raise HTTPException(status_code=404, detail="Metrics endpoint disabled")
    telemetry = getattr(request.app.state, "telemetry", None)
    if telemetry is None:
        raise HTTPException(status_code=503, detail="Telemetry unavailable")
    return telemetry.snapshot()
