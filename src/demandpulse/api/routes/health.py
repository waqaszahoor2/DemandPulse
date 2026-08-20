"""Liveness and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from demandpulse import __version__
from demandpulse.api.dependencies import get_model_service
from demandpulse.api.model_service import ModelService
from demandpulse.api.schemas import HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(service: ModelService = Depends(get_model_service)) -> HealthResponse:
    """Liveness probe: the API process is alive, independent of model readiness."""
    return HealthResponse(
        status="healthy",
        service="DemandPulse",
        version=__version__,
        models_loaded=service.models_loaded,
    )


@router.get("/ready", response_model=ReadinessResponse, responses={503: {"model": ReadinessResponse}})
def ready(service: ModelService = Depends(get_model_service)) -> ReadinessResponse | JSONResponse:
    """Readiness probe: required models are loaded and predictions can be served."""
    report = service.readiness_report()
    payload = ReadinessResponse(
        status="ready" if bool(report["ready"]) else "not_ready",
        service="DemandPulse",
        version=__version__,
        models_loaded=report["models_loaded"],
        required_components=list(report["required_components"]),
        missing_components=list(report["missing_components"]),
    )
    if not report["ready"]:
        return JSONResponse(status_code=503, content=payload.model_dump())
    return payload
