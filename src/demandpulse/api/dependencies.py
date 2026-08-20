"""FastAPI dependency helpers."""

from __future__ import annotations

from fastapi import Request

from demandpulse.api.model_service import ModelService


def get_model_service(request: Request) -> ModelService:
    """Return the application-scoped model service loaded during startup."""
    service = getattr(request.app.state, "model_service", None)
    if service is None:
        raise RuntimeError("Model service was not initialized")
    return service
