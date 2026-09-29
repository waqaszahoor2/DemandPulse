"""Pydantic request/response contracts for the DemandPulse API."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator

Identifier = int | str
NonNegative = Annotated[FiniteFloat, Field(ge=0)]
Probability = Annotated[FiniteFloat, Field(gt=0, lt=1)]
BinaryFlag = Literal[0, 1]


class StrictSchema(BaseModel):
    """Reject undeclared fields so leakage-prone targets cannot enter silently."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ForecastRequest(StrictSchema):
    """Leakage-safe features required for a production point forecast."""

    store_id: Identifier = Field(description="Store identifier")
    product_id: Identifier = Field(description="Product/SKU identifier")
    city_id: Identifier
    management_group_id: Identifier
    first_category_id: Identifier
    second_category_id: Identifier
    third_category_id: Identifier
    forecast_date: date = Field(description="Date being forecast")

    lag_1: NonNegative
    lag_2: NonNegative
    lag_3: NonNegative
    lag_7: NonNegative
    lag_14: NonNegative
    lag_28: NonNegative

    rolling_mean_7: NonNegative
    rolling_mean_14: NonNegative
    rolling_mean_28: NonNegative
    rolling_std_7: NonNegative
    rolling_std_14: NonNegative
    rolling_std_28: NonNegative
    rolling_min_7: NonNegative
    rolling_max_7: NonNegative

    stockout_lag_1: NonNegative
    stockout_lag_7: NonNegative
    discount: Annotated[FiniteFloat, Field(ge=0, le=1)] = Field(
        description="Planned discount multiplier; 1 means no discount"
    )
    holiday_flag: BinaryFlag
    activity_flag: BinaryFlag = Field(description="Known/planned activity flag")

    @model_validator(mode="after")
    def validate_rolling_range(self) -> ForecastRequest:
        if self.rolling_min_7 > self.rolling_max_7:
            raise ValueError("rolling_min_7 cannot exceed rolling_max_7")
        return self


class ForecastResponse(StrictSchema):
    store_id: Identifier
    product_id: Identifier
    forecast_date: date
    prediction: NonNegative
    model_version: str


class ProbabilisticForecastRequest(ForecastRequest):
    horizon: Annotated[int, Field(ge=1, le=7)] = Field(description="Direct forecast horizon in days")


class ProbabilisticForecastResponse(StrictSchema):
    store_id: Identifier
    product_id: Identifier
    forecast_date: date
    p10: NonNegative
    p50: NonNegative
    p90: NonNegative
    interval_lower: NonNegative
    interval_upper: NonNegative
    horizon: int
    model_version: str
    conformal_applied: bool

    @model_validator(mode="after")
    def validate_interval_order(self) -> ProbabilisticForecastResponse:
        if not self.p10 <= self.p50 <= self.p90:
            raise ValueError("response quantiles must satisfy P10 <= P50 <= P90")
        if self.interval_lower > self.interval_upper:
            raise ValueError("interval_lower cannot exceed interval_upper")
        return self


class PromotionEffectRequest(StrictSchema):
    """Pre-treatment feature context used by the observational causal model."""

    store_id: Identifier
    product_id: Identifier
    city_id: Identifier
    management_group_id: Identifier
    first_category_id: Identifier
    second_category_id: Identifier
    third_category_id: Identifier
    date: date

    lag_1: NonNegative
    lag_7: NonNegative
    lag_14: NonNegative
    lag_28: NonNegative
    rolling_mean_7: NonNegative
    rolling_mean_28: NonNegative
    rolling_std_7: NonNegative
    rolling_std_28: NonNegative
    stockout_lag_1: NonNegative
    stockout_lag_7: NonNegative
    holiday_flag: BinaryFlag

    precpt: FiniteFloat | None = None
    avg_temperature: FiniteFloat | None = None
    avg_humidity: FiniteFloat | None = None
    avg_wind_level: FiniteFloat | None = None


class PromotionEffectResponse(StrictSchema):
    store_id: Identifier
    product_id: Identifier
    estimated_treatment_effect: FiniteFloat
    effect_type: str
    ci_lower: FiniteFloat | None = None
    ci_upper: FiniteFloat | None = None
    model_version: str
    warning: str


class InventoryRequest(StrictSchema):
    p10: NonNegative
    p50: NonNegative
    p90: NonNegative
    current_inventory: NonNegative
    service_level: Probability
    holding_cost: NonNegative
    stockout_cost: NonNegative
    lead_time_days: Annotated[FiniteFloat, Field(gt=0)] = 1.0

    @model_validator(mode="after")
    def validate_quantiles_and_costs(self) -> InventoryRequest:
        if not self.p10 <= self.p50 <= self.p90:
            raise ValueError("P10 <= P50 <= P90 is required")
        if self.holding_cost + self.stockout_cost <= 0:
            raise ValueError("holding_cost + stockout_cost must be positive")
        return self


class InventoryResponse(StrictSchema):
    recommended_order_quantity: NonNegative
    recommended_inventory_position: NonNegative
    reorder_point: NonNegative
    safety_stock: NonNegative
    stockout_risk: Annotated[FiniteFloat, Field(ge=0, le=1)]
    assumptions: list[str]


class HealthResponse(StrictSchema):
    status: Literal["healthy"]
    service: str
    version: str
    models_loaded: dict[str, bool]


class ReadinessResponse(StrictSchema):
    status: Literal["ready", "not_ready"]
    service: str
    version: str
    models_loaded: dict[str, bool]
    required_components: list[str]
    missing_components: list[str]


class ModelInfoItem(StrictSchema):
    model_name: str
    model_type: str
    version: str
    training_date: str | None = None
    supported_forecast_horizon: int | list[int] | None = None
    metrics: dict[str, float] = Field(default_factory=dict)
    status: str


class ModelInfoResponse(StrictSchema):
    models: list[ModelInfoItem]


class ErrorResponse(StrictSchema):
    detail: str
    request_id: str | None = None
