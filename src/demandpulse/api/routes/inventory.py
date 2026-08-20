"""Inventory decision route."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from demandpulse.api.dependencies import get_model_service
from demandpulse.api.model_service import ModelService
from demandpulse.api.schemas import InventoryRequest, InventoryResponse

router = APIRouter(tags=["inventory"])


@router.post("/inventory/recommendation", response_model=InventoryResponse)
def inventory_recommendation(
    payload: InventoryRequest,
    service: ModelService = Depends(get_model_service),
) -> InventoryResponse:
    """Convert quantile forecasts and caller-supplied costs into an inventory recommendation."""
    result = service.recommend_inventory(payload.model_dump())
    return InventoryResponse(**result)
