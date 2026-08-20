"""Central project configuration for DemandPulse."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


REQUIRED_COLUMNS: tuple[str, ...] = (
    "city_id",
    "store_id",
    "management_group_id",
    "first_category_id",
    "second_category_id",
    "third_category_id",
    "product_id",
    "dt",
    "sale_amount",
    "hours_sale",
    "stock_hour6_22_cnt",
    "hours_stock_status",
    "discount",
    "holiday_flag",
    "activity_flag",
    "precpt",
    "avg_temperature",
    "avg_humidity",
    "avg_wind_level",
)

MATERIALIZED_COLUMNS: tuple[str, ...] = tuple(
    column for column in REQUIRED_COLUMNS if column not in {"hours_sale", "hours_stock_status"}
)

SERIES_KEYS: tuple[str, str] = ("store_id", "product_id")

CATEGORICAL_FEATURES: tuple[str, ...] = (
    "city_id",
    "store_id",
    "management_group_id",
    "first_category_id",
    "second_category_id",
    "third_category_id",
    "product_id",
)

CALENDAR_FEATURES: tuple[str, ...] = (
    "day_of_week",
    "day_of_month",
    "week_of_year",
    "month",
    "is_weekend",
)

LAG_FEATURES: tuple[str, ...] = (
    "lag_1",
    "lag_2",
    "lag_3",
    "lag_7",
    "lag_14",
    "lag_28",
)

ROLLING_FEATURES: tuple[str, ...] = (
    "rolling_mean_7",
    "rolling_mean_14",
    "rolling_mean_28",
    "rolling_std_7",
    "rolling_std_14",
    "rolling_std_28",
    "rolling_min_7",
    "rolling_max_7",
)

STOCKOUT_HISTORY_FEATURES: tuple[str, ...] = ("stockout_lag_1", "stockout_lag_7")
KNOWN_EXOGENOUS_FEATURES: tuple[str, ...] = (
    "discount",
    "discount_pct",
    "holiday_flag",
    "activity_flag",
)

POINT_FEATURES: tuple[str, ...] = (
    *CALENDAR_FEATURES,
    *LAG_FEATURES,
    *ROLLING_FEATURES,
    *STOCKOUT_HISTORY_FEATURES,
    *KNOWN_EXOGENOUS_FEATURES,
    *CATEGORICAL_FEATURES,
)

CAUSAL_PRETREATMENT_FEATURES: tuple[str, ...] = (
    "lag_1",
    "lag_7",
    "lag_14",
    "lag_28",
    "rolling_mean_7",
    "rolling_mean_28",
    "rolling_std_7",
    "rolling_std_28",
    "stockout_lag_1",
    "stockout_lag_7",
    "day_of_week",
    "month",
    "is_weekend",
    "holiday_flag",
    *CATEGORICAL_FEATURES,
)

WEATHER_FEATURES: tuple[str, ...] = (
    "precpt",
    "avg_temperature",
    "avg_humidity",
    "avg_wind_level",
)


@dataclass(frozen=True)
class DemandPulseConfig:
    """Centralized configuration shared by production modules."""

    dataset_id: str = "Dingdong-Inc/FreshRetailNet-50K"
    random_state: int = 42
    forecast_horizon: int = 7
    series_sample_percent: float = 30.0
    quantiles: tuple[float, float, float] = (0.10, 0.50, 0.90)
    api_version: str = "0.4.0"
    mlflow_tracking_uri: str = field(
        default_factory=lambda: os.environ.get(
            "MLFLOW_TRACKING_URI",
            (Path(os.environ.get("DEMANDPULSE_PROJECT_ROOT", ".")).resolve() / "mlruns").as_uri(),
        )
    )
    mlflow_experiment_name: str = field(
        default_factory=lambda: os.environ.get("MLFLOW_EXPERIMENT_NAME", "demandpulse-point-forecasting")
    )
    model_dir_override: str | None = field(default_factory=lambda: os.environ.get("MODEL_DIR"))
    app_env: str = field(default_factory=lambda: os.environ.get("APP_ENV", "development").lower())
    log_level: str = field(default_factory=lambda: os.environ.get("LOG_LEVEL", "INFO").upper())
    api_host: str = field(default_factory=lambda: os.environ.get("API_HOST", "0.0.0.0"))
    api_port: int = field(default_factory=lambda: int(os.environ.get("PORT", os.environ.get("API_PORT", "8000"))))
    model_source: str = field(default_factory=lambda: os.environ.get("DEMANDPULSE_MODEL_SOURCE", "local").lower())
    model_bundle_uri: str | None = field(default_factory=lambda: os.environ.get("MODEL_BUNDLE_URI") or None)
    required_model_components: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            part.strip()
            for part in os.environ.get("REQUIRED_MODEL_COMPONENTS", "point,probabilistic").split(",")
            if part.strip()
        )
    )
    log_json: bool = field(
        default_factory=lambda: os.environ.get("LOG_FORMAT", "json").lower() == "json"
    )
    request_timeout_seconds: float = field(
        default_factory=lambda: float(os.environ.get("REQUEST_TIMEOUT_SECONDS", "25"))
    )
    max_request_bytes: int = field(
        default_factory=lambda: int(os.environ.get("MAX_REQUEST_BYTES", str(256 * 1024)))
    )
    metrics_enabled: bool = field(
        default_factory=lambda: os.environ.get("METRICS_ENABLED", "true").lower() in {"1", "true", "yes"}
    )
    prediction_log_path: str | None = field(
        default_factory=lambda: os.environ.get("PREDICTION_LOG_PARQUET") or None
    )
    interval_alpha: float = 0.20
    stream_batch_size: int = 50_000
    project_root: Path = field(
        default_factory=lambda: Path(os.environ.get("DEMANDPULSE_PROJECT_ROOT", ".")).resolve()
    )
    required_columns: tuple[str, ...] = REQUIRED_COLUMNS
    materialized_columns: tuple[str, ...] = MATERIALIZED_COLUMNS
    series_keys: tuple[str, str] = SERIES_KEYS
    categorical_features: tuple[str, ...] = CATEGORICAL_FEATURES
    point_features: tuple[str, ...] = POINT_FEATURES
    causal_pretreatment_features: tuple[str, ...] = CAUSAL_PRETREATMENT_FEATURES
    weather_features: tuple[str, ...] = WEATHER_FEATURES
    point_lgbm_params: dict[str, Any] = field(
        default_factory=lambda: {
            "objective": "regression_l1",
            "learning_rate": 0.05,
            "n_estimators": 800,
            "num_leaves": 63,
            "min_child_samples": 40,
            "subsample": 0.9,
            "colsample_bytree": 0.9,
            "reg_alpha": 0.1,
            "reg_lambda": 0.1,
            "random_state": 42,
            "n_jobs": -1,
            "verbosity": -1,
        }
    )
    quantile_lgbm_params: dict[str, Any] = field(
        default_factory=lambda: {
            "learning_rate": 0.05,
            "n_estimators": 1000,
            "num_leaves": 63,
            "min_child_samples": 40,
            "subsample": 0.9,
            "colsample_bytree": 0.9,
            "reg_alpha": 0.1,
            "reg_lambda": 0.1,
            "random_state": 42,
            "n_jobs": -1,
            "verbosity": -1,
        }
    )

    @property
    def models_dir(self) -> Path:
        if self.model_dir_override:
            return Path(self.model_dir_override).expanduser().resolve()
        return self.project_root / "models"

    @property
    def reports_dir(self) -> Path:
        return self.project_root / "reports"

    @property
    def tables_dir(self) -> Path:
        return self.reports_dir / "tables"

    @property
    def figures_dir(self) -> Path:
        return self.reports_dir / "figures"

    @property
    def point_model_path(self) -> Path:
        return self.models_dir / "demandpulse_lgbm.txt"

    @property
    def quantile_models_dir(self) -> Path:
        return self.models_dir / "quantile"


DEFAULT_CONFIG = DemandPulseConfig()
