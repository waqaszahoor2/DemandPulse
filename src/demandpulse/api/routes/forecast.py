"""Point and probabilistic forecasting routes."""

from __future__ import annotations

from time import perf_counter

from fastapi import APIRouter, Depends, Request

from demandpulse.api.dependencies import get_model_service
from demandpulse.api.model_service import ModelService
from demandpulse.api.schemas import (
    ForecastRequest,
    ForecastResponse,
    ProbabilisticForecastRequest,
    ProbabilisticForecastResponse,
)
from demandpulse.monitoring.prediction_log import PredictionLogRecord
from demandpulse.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["forecasting"])


def _record_prediction(request: Request, record: PredictionLogRecord) -> None:
    prediction_logger = getattr(request.app.state, "prediction_logger", None)
    if prediction_logger is not None:
        prediction_logger.log(record)


@router.post("/forecast", response_model=ForecastResponse)
def point_forecast(
    payload: ForecastRequest,
    request: Request,
    service: ModelService = Depends(get_model_service),
) -> ForecastResponse:
    """Generate a non-negative next-step point forecast from prediction-time-safe features."""
    start = perf_counter()
    result = service.predict_point_forecast(payload.model_dump())
    latency_ms = (perf_counter() - start) * 1000
    telemetry = getattr(request.app.state, "telemetry", None)
    if telemetry is not None:
        telemetry.record_prediction("point", prediction=result["prediction"])
    _record_prediction(
        request,
        PredictionLogRecord.create(
            request_id=getattr(request.state, "request_id", "unknown"),
            store_id=payload.store_id,
            product_id=payload.product_id,
            forecast_date=payload.forecast_date,
            horizon=1,
            p50=result["prediction"],
            model_version=result["model_version"],
        ),
    )
    logger.info(
        "point_forecast_completed",
        extra={
            "request_id": getattr(request.state, "request_id", "unknown"),
            "model_version": result["model_version"],
            "latency_ms": round(latency_ms, 3),
        },
    )
    return ForecastResponse(
        store_id=payload.store_id,
        product_id=payload.product_id,
        forecast_date=payload.forecast_date,
        prediction=result["prediction"],
        model_version=result["model_version"],
    )


@router.post("/forecast/probabilistic", response_model=ProbabilisticForecastResponse)
def probabilistic_forecast(
    payload: ProbabilisticForecastRequest,
    request: Request,
    service: ModelService = Depends(get_model_service),
) -> ProbabilisticForecastResponse:
    """Generate repaired P10/P50/P90 and optional conformal interval bounds."""
    start = perf_counter()
    result = service.predict_probabilistic_forecast(payload.model_dump())
    latency_ms = (perf_counter() - start) * 1000
    telemetry = getattr(request.app.state, "telemetry", None)
    if telemetry is not None:
        telemetry.record_prediction(
            "probabilistic",
            p10=result["p10"],
            p50=result["p50"],
            p90=result["p90"],
            interval_width=result["interval_upper"] - result["interval_lower"],
        )
    _record_prediction(
        request,
        PredictionLogRecord.create(
            request_id=getattr(request.state, "request_id", "unknown"),
            store_id=payload.store_id,
            product_id=payload.product_id,
            forecast_date=payload.forecast_date,
            horizon=payload.horizon,
            p10=result["p10"],
            p50=result["p50"],
            p90=result["p90"],
            model_version=result["model_version"],
        ),
    )
    logger.info(
        "probabilistic_forecast_completed",
        extra={
            "request_id": getattr(request.state, "request_id", "unknown"),
            "model_version": result["model_version"],
            "horizon": payload.horizon,
            "latency_ms": round(latency_ms, 3),
        },
    )
    return ProbabilisticForecastResponse(
        store_id=payload.store_id,
        product_id=payload.product_id,
        forecast_date=payload.forecast_date,
        **result,
    )
