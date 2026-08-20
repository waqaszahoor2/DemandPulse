"""Minimal production training entry point used by the Makefile."""

from __future__ import annotations

import argparse

from demandpulse.config import DEFAULT_CONFIG, LAG_FEATURES, ROLLING_FEATURES, STOCKOUT_HISTORY_FEATURES
from demandpulse.data.loader import load_train_data
from demandpulse.data.validation import validate_frame
from demandpulse.features.lag_features import add_lag_features, drop_incomplete_history
from demandpulse.features.time_features import add_time_features
from demandpulse.forecasting.point_model import save_point_model, train_point_model
from demandpulse.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)


def train_command(sample_percent: float, max_rows: int | None) -> None:
    config = DEFAULT_CONFIG
    train = load_train_data(config, sample_percent=sample_percent, max_rows=max_rows)
    validate_frame(
        train,
        required_columns=config.materialized_columns,
        allowed_columns=config.materialized_columns,
    )
    features = add_time_features(train)
    features["discount_pct"] = 1.0 - features["discount"]
    features = add_lag_features(features)
    historical_required = [*LAG_FEATURES, *ROLLING_FEATURES, *STOCKOUT_HISTORY_FEATURES]
    features = drop_incomplete_history(features, historical_required)
    model, metadata = train_point_model(features, config=config)
    save_point_model(model, config.point_model_path, metadata)
    logger.info("Saved point model to %s", config.point_model_path)


def main() -> None:
    parser = argparse.ArgumentParser(prog="demandpulse")
    subparsers = parser.add_subparsers(dest="command", required=True)
    train_parser = subparsers.add_parser("train", help="Train the core global point model")
    train_parser.add_argument("--sample-percent", type=float, default=DEFAULT_CONFIG.series_sample_percent)
    train_parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Development-only cap; leave unset for complete-series production materialization.",
    )
    args = parser.parse_args()
    configure_logging()
    if args.command == "train":
        train_command(args.sample_percent, args.max_rows)


if __name__ == "__main__":
    main()
