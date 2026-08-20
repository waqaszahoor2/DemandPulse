"""Safe model information route."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from demandpulse.api.dependencies import get_model_service
from demandpulse.api.model_service import ModelService
from demandpulse.api.schemas import ModelInfoResponse

router = APIRouter(tags=["models"])


@router.get("/model/info", response_model=ModelInfoResponse)
def model_info(service: ModelService = Depends(get_model_service)) -> ModelInfoResponse:
    """Return safe model metadata only; no paths, credentials, or environment variables."""
    return ModelInfoResponse(models=service.model_info())
