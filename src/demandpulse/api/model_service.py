"""Model loading, caching, prediction routing, and safe model metadata."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import lightgbm as lgb
import numpy as np
import pandas as pd

from demandpulse.causal.treatment_effects import estimate_cate
from demandpulse.config import DEFAULT_CONFIG, DemandPulseConfig
from demandpulse.forecasting.point_model import (
    align_categorical_features,
    load_point_model,
    predict_point,
)
from demandpulse.forecasting.probabilistic import (
    apply_conformal_adjustment,
    predict_quantiles,
    repair_quantile_crossing,
)
from demandpulse.mlops.model_bundle import hydrate_model_bundle
from demandpulse.mlops.registry import get_model_version, load_registered_model
from demandpulse.optimization.inventory import (
    calculate_reorder_point,
    recommend_inventory,
)
from demandpulse.utils.logging import get_logger

logger = get_logger(__name__)

CAUSAL_WARNING = "Observational causal estimate subject to assumptions and residual confounding."


class ModelUnavailableError(RuntimeError):
    """Raised when a required model artifact is unavailable."""


class UnsupportedHorizonError(ValueError):
    """Raised for a forecast horizon outside the supported direct-model range."""


class PredictionInputError(ValueError):
    """Raised when model-required prediction features are unavailable."""


def _sha256_short(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    found = False
    for path in sorted(paths):
        if not path.exists() or not path.is_file():
            continue
        found = True
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    return digest.hexdigest()[:12] if found else "unavailable"


def _metadata_sidecar(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".metadata.json")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))




def _metadata_from_booster(
    booster: lgb.Booster,
    *,
    categorical_candidates: tuple[str, ...],
) -> dict[str, Any]:
    """Recover prediction metadata from a native LightGBM model when no sidecar exists."""
    features = list(booster.feature_name())
    categorical_in_model = [name for name in features if name in categorical_candidates]
    stored_categories = list(getattr(booster, "pandas_categorical", None) or [])
    category_levels: dict[str, list[Any]] = {}
    if stored_categories and len(stored_categories) == len(categorical_in_model):
        category_levels = {
            column: list(levels)
            for column, levels in zip(categorical_in_model, stored_categories)
        }
    return {
        "feature_columns": features,
        "categorical_features": categorical_in_model,
        "category_levels": category_levels,
    }

def _calendar_features(value: pd.Timestamp) -> dict[str, int]:
    iso = value.isocalendar()
    return {
        "day_of_week": int(value.dayofweek),
        "day_of_month": int(value.day),
        "week_of_year": int(iso.week),
        "month": int(value.month),
        "is_weekend": int(value.dayofweek >= 5),
    }


def _prediction_context(payload: Mapping[str, Any], *, date_key: str) -> dict[str, Any]:
    """Create a feature superset containing point and direct-horizon aliases."""
    values = dict(payload)
    raw_date = values.pop(date_key)
    values.pop("horizon", None)
    timestamp = pd.Timestamp(raw_date)
    calendar = _calendar_features(timestamp)
    values.update(calendar)
    if "discount" in values:
        values["discount_pct"] = 1.0 - float(values["discount"])
        values["future_discount"] = values["discount"]
        values["future_discount_pct"] = values["discount_pct"]
    if "holiday_flag" in values:
        values["future_holiday_flag"] = values["holiday_flag"]
    if "activity_flag" in values:
        values["future_activity_flag"] = values["activity_flag"]
    values.update(
        {
            "forecast_day_of_week": calendar["day_of_week"],
            "forecast_day_of_month": calendar["day_of_month"],
            "forecast_week_of_year": calendar["week_of_year"],
            "forecast_month": calendar["month"],
            "forecast_is_weekend": calendar["is_weekend"],
        }
    )
    return values


class ModelService:
    """Load DemandPulse models once and expose prediction-oriented operations."""

    def __init__(self, config: DemandPulseConfig = DEFAULT_CONFIG) -> None:
        self.config = config
        self.point_model: Any | None = None
        self.point_metadata: dict[str, Any] = {}
        self.quantile_models: dict[int, dict[float, tuple[Any, Mapping[str, Any]]]] = {}
        self.conformal_adjustments: dict[str, Any] = {}
        self.causal_models: tuple[Any, Any] | None = None
        self.causal_metadata: dict[str, Any] = {}
        self._model_info: list[dict[str, Any]] = []
        self._loaded_once = False
        self._model_bundle_error: str | None = None

    @property
    def models_loaded(self) -> dict[str, bool]:
        return {
            "point": self.point_model is not None,
            "probabilistic": bool(self.quantile_models),
            "causal": self.causal_models is not None,
        }

    def load_models(self) -> None:
        """Load/capture model artifacts once; missing optional artifacts do not crash liveness."""
        if self._loaded_once:
            return
        self._loaded_once = True
        if self.config.model_bundle_uri:
            try:
                hydrate_model_bundle(
                    self.config.model_bundle_uri,
                    self.config.models_dir,
                    require_manifest=self.config.app_env == "production",
                )
            except Exception as exc:
                logger.error("model_bundle_hydration_failed", extra={"error_type": type(exc).__name__})
                self._model_bundle_error = type(exc).__name__
                return
        if self.config.model_source == "mlflow":
            self._load_point_from_mlflow()
        else:
            self._load_point_local()
        self._load_quantile_local()
        self._load_causal_local()
        self._load_safe_metrics()

    def readiness_report(self) -> dict[str, object]:
        """Return model readiness for configured required serving components."""
        loaded = self.models_loaded
        required = tuple(self.config.required_model_components)
        unknown = sorted(set(required) - set(loaded))
        if unknown:
            return {
                "ready": False,
                "required_components": list(required),
                "models_loaded": loaded,
                "missing_components": unknown,
                "reason": "unknown required model component configured",
            }
        missing = [name for name in required if not loaded.get(name, False)]
        return {
            "ready": not missing,
            "required_components": list(required),
            "models_loaded": loaded,
            "missing_components": missing,
            "reason": (
                f"model bundle hydration failed: {self._model_bundle_error}"
                if self._model_bundle_error
                else (None if not missing else "required model artifacts are not loaded")
            ),
        }

    @property
    def serving_model_version(self) -> str:
        """Return a low-cardinality version identifier for request logs."""
        if self.point_model is not None:
            return str(self.point_metadata.get("model_version", "unknown"))
        if self.quantile_models:
            return str(getattr(self, "_quantile_version", "unknown"))
        return "unavailable"

    def _load_point_local(self) -> None:
        path = self.config.point_model_path
        if not path.exists():
            logger.warning("Point model unavailable; /forecast will return service unavailable")
            return
        meta_path = _metadata_sidecar(path)
        if meta_path.exists():
            model, metadata = load_point_model(path)
        else:
            model = lgb.Booster(model_file=str(path))
            metadata = _metadata_from_booster(
                model, categorical_candidates=self.config.categorical_features
            )
            logger.info("Point metadata sidecar absent; recovered feature contract from LightGBM model")
        self.point_model = model
        self.point_metadata = dict(metadata)
        self.point_metadata.setdefault("model_version", _sha256_short([path, _metadata_sidecar(path)]))
        self.point_metadata.setdefault("model_name", "demandpulse-point-forecast")
        self.point_metadata.setdefault("model_type", "LightGBM point forecast")
        self.point_metadata.setdefault("status", "local")

    def _load_point_from_mlflow(self) -> None:
        model_name = "demandpulse-point-forecast"
        try:
            registered = get_model_version(model_name, alias="champion", config=self.config)
            model = load_registered_model(model_name, alias="champion", config=self.config)
        except Exception as exc:  # MLflow client errors vary by backend/version.
            logger.warning("MLflow champion point model unavailable: %s", exc)
            return
        self.point_model = model
        self.point_metadata = {
            "feature_columns": list(self.config.point_features),
            "category_levels": {},
            "model_version": str(getattr(registered, "version", "unknown")),
            "model_name": model_name,
            "model_type": "MLflow registered point forecast",
            "status": "champion",
            "training_timestamp": (str(getattr(registered, "creation_timestamp")) if getattr(registered, "creation_timestamp", None) is not None else None),
        }

    def _load_quantile_local(self) -> None:
        model_dir = self.config.quantile_models_dir
        paths: list[Path] = []
        for horizon in range(1, self.config.forecast_horizon + 1):
            models: dict[float, tuple[Any, Mapping[str, Any]]] = {}
            for quantile in self.config.quantiles:
                q_int = int(round(quantile * 100))
                path = model_dir / f"h{horizon:02d}_q{q_int:02d}.txt"
                meta_path = _metadata_sidecar(path)
                if not path.exists():
                    models = {}
                    break
                model = lgb.Booster(model_file=str(path))
                if meta_path.exists():
                    metadata = _load_json(meta_path)
                    paths.extend([path, meta_path])
                else:
                    metadata = _metadata_from_booster(
                        model, categorical_candidates=self.config.categorical_features
                    )
                    paths.append(path)
                metadata.setdefault("quantile", quantile)
                models[float(quantile)] = (model, metadata)
            if models:
                self.quantile_models[horizon] = models

        adjustment_path = model_dir / "conformal_adjustments.json"
        if adjustment_path.exists():
            self.conformal_adjustments = _load_json(adjustment_path)
            paths.append(adjustment_path)
        if self.quantile_models:
            self._quantile_version = _sha256_short(paths)
        else:
            self._quantile_version = "unavailable"
            logger.warning("Quantile models unavailable; probabilistic endpoint will return service unavailable")

    def _load_causal_local(self) -> None:
        causal_dir = self.config.models_dir / "causal"
        treated_path = causal_dir / "outcome_treated.txt"
        control_path = causal_dir / "outcome_control.txt"
        treated_meta = _metadata_sidecar(treated_path)
        control_meta = _metadata_sidecar(control_path)
        if not treated_path.exists() or not control_path.exists():
            logger.warning("Causal outcome models unavailable; promotion endpoint will return service unavailable")
            return
        treated_model = lgb.Booster(model_file=str(treated_path))
        control_model = lgb.Booster(model_file=str(control_path))
        self.causal_models = (treated_model, control_model)
        metadata = (
            _load_json(treated_meta)
            if treated_meta.exists()
            else _metadata_from_booster(treated_model, categorical_candidates=self.config.categorical_features)
        )
        control_metadata = (
            _load_json(control_meta)
            if control_meta.exists()
            else _metadata_from_booster(control_model, categorical_candidates=self.config.categorical_features)
        )
        if metadata.get("feature_columns") != control_metadata.get("feature_columns"):
            logger.error("Causal treated/control model feature metadata do not match")
            self.causal_models = None
            return
        self.causal_metadata = metadata
        self.causal_metadata["model_version"] = _sha256_short(
            [treated_path, control_path, *(p for p in [treated_meta, control_meta] if p.exists())]
        )
        self.causal_metadata.setdefault("model_name", "demandpulse-causal-tlearner")
        self.causal_metadata.setdefault("model_type", "LightGBM T-learner CATE")
        self.causal_metadata.setdefault("status", "observational")

    def _load_safe_metrics(self) -> None:
        """Load report metrics for metadata only; never use them as prediction inputs."""
        metrics_by_name: dict[str, dict[str, float]] = {}
        point_path = self.config.tables_dir / "final_model_comparison.csv"
        if point_path.exists():
            try:
                frame = pd.read_csv(point_path)
                row = frame.loc[frame["model"].astype(str).eq("LightGBM")]
                if not row.empty:
                    metrics_by_name["point"] = {
                        key: float(row.iloc[0][key])
                        for key in ["MAE", "RMSE", "WAPE", "Bias"]
                        if key in row.columns and pd.notna(row.iloc[0][key])
                    }
            except (OSError, ValueError, KeyError) as exc:
                logger.warning("Could not read point report metrics: %s", exc)
        prob_path = self.config.tables_dir / "probabilistic_final_metrics.csv"
        if prob_path.exists():
            try:
                frame = pd.read_csv(prob_path)
                row = frame.loc[frame["model"].astype(str).str.contains("Conformal", case=False, na=False)]
                if not row.empty:
                    metrics_by_name["probabilistic"] = {
                        key: float(row.iloc[0][key])
                        for key in ["mae", "wape", "mean_pinball", "coverage", "mean_width", "interval_score"]
                        if key in row.columns and pd.notna(row.iloc[0][key])
                    }
            except (OSError, ValueError, KeyError) as exc:
                logger.warning("Could not read probabilistic report metrics: %s", exc)
        self._safe_metrics = metrics_by_name

    def _require_features(self, context: Mapping[str, Any], metadata: Mapping[str, Any]) -> pd.DataFrame:
        features = list(metadata.get("feature_columns", ()))
        if not features:
            raise PredictionInputError("Model metadata does not define required features")
        missing = sorted(set(features) - set(context))
        if missing:
            raise PredictionInputError(f"Prediction context is missing model-required features: {missing}")
        return pd.DataFrame([{feature: context[feature] for feature in features}])

    def predict_point_forecast(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        if self.point_model is None:
            raise ModelUnavailableError("Point forecasting model is unavailable")
        context = _prediction_context(payload, date_key="forecast_date")
        frame = self._require_features(context, self.point_metadata)
        prediction = float(predict_point(self.point_model, frame, self.point_metadata)[0])
        return {
            "prediction": max(prediction, 0.0),
            "model_version": str(self.point_metadata.get("model_version", "unknown")),
        }

    def _conformal_qhat(self, horizon: int) -> float | None:
        candidates = [
            str(horizon),
            f"h{horizon:02d}",
            f"horizon_{horizon}",
        ]
        for key in candidates:
            if key not in self.conformal_adjustments:
                continue
            value = self.conformal_adjustments[key]
            if isinstance(value, Mapping):
                value = value.get("q_hat", value.get("adjustment"))
            if value is None:
                continue
            q_hat = float(value)
            if np.isfinite(q_hat) and q_hat >= 0:
                return q_hat
        return None

    def predict_probabilistic_forecast(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        horizon = int(payload["horizon"])
        if horizon < 1 or horizon > self.config.forecast_horizon:
            raise UnsupportedHorizonError(
                f"Supported forecast horizons are 1-{self.config.forecast_horizon}"
            )
        models = self.quantile_models.get(horizon)
        if not models:
            raise ModelUnavailableError(f"Probabilistic models for horizon {horizon} are unavailable")
        context = _prediction_context(payload, date_key="forecast_date")
        # Validate all horizon models against the request context before predicting.
        first_metadata = next(iter(models.values()))[1]
        self._require_features(context, first_metadata)
        frame = pd.DataFrame([context])
        raw = predict_quantiles(models, frame, clip_nonnegative=False)
        repaired = repair_quantile_crossing(raw)
        repaired[["p10", "p50", "p90"]] = repaired[["p10", "p50", "p90"]].clip(lower=0.0)
        p10, p50, p90 = (float(repaired.iloc[0][name]) for name in ["p10", "p50", "p90"])
        q_hat = self._conformal_qhat(horizon)
        if q_hat is None:
            lower, upper = p10, p90
            conformal_applied = False
        else:
            lo, hi = apply_conformal_adjustment([p10], [p90], q_hat)
            lower, upper = float(lo[0]), float(hi[0])
            conformal_applied = True
        return {
            "p10": p10,
            "p50": p50,
            "p90": p90,
            "interval_lower": max(lower, 0.0),
            "interval_upper": max(upper, 0.0),
            "horizon": horizon,
            "model_version": self._quantile_version,
            "conformal_applied": conformal_applied,
        }

    def predict_promotion_effect(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        if self.causal_models is None:
            raise ModelUnavailableError("Causal promotion models are unavailable")
        context = _prediction_context(payload, date_key="date")
        frame = self._require_features(context, self.causal_metadata)
        category_levels = self.causal_metadata.get("category_levels", {})
        if category_levels:
            frame = align_categorical_features(frame, category_levels)
        treated, control = self.causal_models
        effect = float(estimate_cate(treated, control, frame)[0])
        ci_lower = self.causal_metadata.get("cate_ci_lower")
        ci_upper = self.causal_metadata.get("cate_ci_upper")
        return {
            "estimated_treatment_effect": effect,
            "effect_type": "CATE",
            "ci_lower": float(ci_lower) if ci_lower is not None else None,
            "ci_upper": float(ci_upper) if ci_upper is not None else None,
            "model_version": str(self.causal_metadata.get("model_version", "unknown")),
            "warning": CAUSAL_WARNING,
        }

    def recommend_inventory(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        recommendation = recommend_inventory(
            float(payload["p10"]),
            float(payload["p50"]),
            float(payload["p90"]),
            service_level=float(payload["service_level"]),
            holding_cost=float(payload["holding_cost"]),
            stockout_cost=float(payload["stockout_cost"]),
        )
        inventory_position = float(recommendation["recommended_quantity"])
        current_inventory = float(payload["current_inventory"])
        order_quantity = max(inventory_position - current_inventory, 0.0)
        reorder_point = calculate_reorder_point(
            float(payload["p50"]),
            float(recommendation["safety_stock"]),
            lead_time_days=float(payload.get("lead_time_days", 1.0)),
        )
        return {
            "recommended_order_quantity": order_quantity,
            "recommended_inventory_position": inventory_position,
            "reorder_point": reorder_point,
            "safety_stock": float(recommendation["safety_stock"]),
            "stockout_risk": float(recommendation["stockout_probability"]),
            "assumptions": [
                "P10/P50/P90 are treated as conditional demand quantiles.",
                "Holding and stockout costs are caller-supplied decision assumptions.",
                "Reorder point uses P50 as expected daily demand over the supplied lead time.",
                "No automatic promotion uplift is added by this endpoint.",
            ],
        }

    def model_info(self) -> list[dict[str, Any]]:
        """Return safe public metadata without filesystem paths or environment variables."""
        info: list[dict[str, Any]] = []
        if self.point_model is not None:
            info.append({
                "model_name": str(self.point_metadata.get("model_name", "demandpulse-point-forecast")),
                "model_type": str(self.point_metadata.get("model_type", "LightGBM point forecast")),
                "version": str(self.point_metadata.get("model_version", "unknown")),
                "training_date": self.point_metadata.get("training_timestamp"),
                "supported_forecast_horizon": self.config.forecast_horizon,
                "metrics": self._safe_metrics.get("point", {}),
                "status": str(self.point_metadata.get("status", "loaded")),
            })
        if self.quantile_models:
            info.append({
                "model_name": "demandpulse-probabilistic",
                "model_type": "Direct-horizon LightGBM quantile ensemble",
                "version": self._quantile_version,
                "training_date": None,
                "supported_forecast_horizon": sorted(self.quantile_models),
                "metrics": self._safe_metrics.get("probabilistic", {}),
                "status": "loaded",
            })
        if self.causal_models is not None:
            info.append({
                "model_name": str(self.causal_metadata.get("model_name", "demandpulse-causal-tlearner")),
                "model_type": str(self.causal_metadata.get("model_type", "CATE T-learner")),
                "version": str(self.causal_metadata.get("model_version", "unknown")),
                "training_date": self.causal_metadata.get("training_timestamp"),
                "supported_forecast_horizon": None,
                "metrics": {},
                "status": str(self.causal_metadata.get("status", "observational")),
            })
        return info
