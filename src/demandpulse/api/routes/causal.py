"""Observational promotion-effect route."""

from __future__ import annotations

from time import perf_counter

from fastapi import APIRouter, Depends, Request

from demandpulse.api.dependencies import get_model_service
from demandpulse.api.model_service import ModelService
from demandpulse.api.schemas import PromotionEffectRequest, PromotionEffectResponse
from demandpulse.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["causal"])


@router.post("/promotion-effect", response_model=PromotionEffectResponse)
def promotion_effect(
    payload: PromotionEffectRequest,
    request: Request,
    service: ModelService = Depends(get_model_service),
) -> PromotionEffectResponse:
    """Estimate conditional promotional effect from pre-treatment covariates."""
    start = perf_counter()
    result = service.predict_promotion_effect(payload.model_dump())
    logger.info(
        "promotion_effect success request_id=%s model_version=%s latency_ms=%.3f",
        getattr(request.state, "request_id", "unknown"),
        result["model_version"],
        (perf_counter() - start) * 1000,
    )
    return PromotionEffectResponse(
        store_id=payload.store_id,
        product_id=payload.product_id,
        **result,
    )
