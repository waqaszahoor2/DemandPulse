"""DemandPulse FastAPI application factory."""

from __future__ import annotations

import asyncio
import re
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from demandpulse import __version__
from demandpulse.api.model_service import (
    ModelService,
    ModelUnavailableError,
    PredictionInputError,
    UnsupportedHorizonError,
)
from demandpulse.api.routes import causal, forecast, health, inventory, metrics, models
from demandpulse.api.schemas import ErrorResponse
from demandpulse.config import DEFAULT_CONFIG, DemandPulseConfig
from demandpulse.monitoring.prediction_log import PredictionLogger
from demandpulse.monitoring.telemetry import TelemetryStore
from demandpulse.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def _request_id(header_value: str | None) -> str:
    if header_value and _REQUEST_ID_RE.fullmatch(header_value):
        return header_value
    return str(uuid.uuid4())


def create_app(
    *,
    config: DemandPulseConfig = DEFAULT_CONFIG,
    model_service: Any | None = None,
) -> FastAPI:
    """Create the API with one application-scoped model service and observability state."""
    configure_logging(config.log_level, json_output=config.log_json)
    service = model_service or ModelService(config)
    telemetry = TelemetryStore()
    prediction_logger = PredictionLogger(local_parquet_path=config.prediction_log_path)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info(
            "service_starting",
            extra={"service": "DemandPulse", "app_version": __version__, "app_env": config.app_env},
        )
        app.state.model_service = service
        app.state.telemetry = telemetry
        app.state.prediction_logger = prediction_logger
        app.state.metrics_enabled = config.metrics_enabled
        service.load_models()
        readiness = (
            service.readiness_report()
            if hasattr(service, "readiness_report")
            else {"ready": all(service.models_loaded.values())}
        )
        logger.info(
            "service_model_readiness",
            extra={
                "ready": bool(readiness.get("ready", False)),
                "model_version": getattr(service, "serving_model_version", "unknown"),
            },
        )
        yield
        prediction_logger.flush()
        logger.info("service_stopping", extra={"service": "DemandPulse"})

    application = FastAPI(
        title="DemandPulse API",
        version=__version__,
        description=(
            "Production API for DemandPulse point/probabilistic forecasting, "
            "observational promotion-effect estimates, inventory decisions, and safe model metadata."
        ),
        lifespan=lifespan,
    )

    @application.middleware("http")
    async def production_guardrails(request: Request, call_next: Any) -> Any:
        request_id = _request_id(request.headers.get("X-Request-ID"))
        request.state.request_id = request_id
        start = time.perf_counter()
        content_length = request.headers.get("content-length")
        too_large = False
        if content_length:
            try:
                too_large = int(content_length) > config.max_request_bytes
            except ValueError:
                too_large = True
        elif request.method in {"POST", "PUT", "PATCH"}:
            body = await request.body()
            too_large = len(body) > config.max_request_bytes
        if too_large:
            response = JSONResponse(
                status_code=413,
                content=ErrorResponse(
                    detail="Request body exceeds configured size limit", request_id=request_id
                ).model_dump(),
            )
            response.headers["X-Request-ID"] = request_id
            telemetry.record_request(request.url.path, 413, (time.perf_counter() - start) * 1000)
            return response

        try:
            response = await asyncio.wait_for(call_next(request), timeout=config.request_timeout_seconds)
        except TimeoutError:
            latency_ms = (time.perf_counter() - start) * 1000
            telemetry.record_request(request.url.path, 504, latency_ms)
            logger.error(
                "request_timeout",
                extra={
                    "request_id": request_id,
                    "endpoint": request.url.path,
                    "http_status": 504,
                    "latency_ms": round(latency_ms, 3),
                },
            )
            response = JSONResponse(
                status_code=504,
                content=ErrorResponse(detail="Request timed out", request_id=request_id).model_dump(),
            )
        except Exception:
            logger.exception("request_failed", extra={"request_id": request_id, "endpoint": request.url.path})
            raise

        latency_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        telemetry.record_request(request.url.path, response.status_code, latency_ms)
        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "endpoint": request.url.path,
                "http_status": response.status_code,
                "latency_ms": round(latency_ms, 3),
                "model_version": getattr(service, "serving_model_version", "unknown"),
                "prediction_status": "success" if response.status_code < 400 else "failure",
            },
        )
        return response

    def error_payload(request: Request, detail: str) -> dict[str, str | None]:
        return ErrorResponse(
            detail=detail, request_id=getattr(request.state, "request_id", None)
        ).model_dump()

    @application.exception_handler(ModelUnavailableError)
    async def unavailable_handler(request: Request, exc: ModelUnavailableError) -> JSONResponse:
        return JSONResponse(status_code=503, content=error_payload(request, str(exc)))

    @application.exception_handler(UnsupportedHorizonError)
    async def horizon_handler(request: Request, exc: UnsupportedHorizonError) -> JSONResponse:
        return JSONResponse(status_code=400, content=error_payload(request, str(exc)))

    @application.exception_handler(PredictionInputError)
    async def input_handler(request: Request, exc: PredictionInputError) -> JSONResponse:
        return JSONResponse(status_code=400, content=error_payload(request, str(exc)))

    @application.exception_handler(Exception)
    async def unexpected_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unexpected_server_error",
            extra={
                "request_id": getattr(request.state, "request_id", "unknown"),
                "endpoint": request.url.path,
            },
        )
        return JSONResponse(status_code=500, content=error_payload(request, "Unexpected server failure"))

    for router in [
        health.router,
        forecast.router,
        causal.router,
        inventory.router,
        models.router,
        metrics.router,
    ]:
        application.include_router(router)
        application.include_router(router, prefix="/api")
    return application


app = create_app()
