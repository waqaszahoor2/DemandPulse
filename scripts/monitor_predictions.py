"""Batch forecast-performance monitor for persisted prediction/actual Parquet files."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from demandpulse.monitoring.production import forecast_performance_by_group


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--actuals", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--groups", default="model_version,horizon")
    args = parser.parse_args()

    predictions = pd.read_parquet(args.predictions)
    actuals = pd.read_parquet(args.actuals)
    groups = tuple(value.strip() for value in args.groups.split(",") if value.strip())
    result = forecast_performance_by_group(predictions, actuals, group_columns=groups)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
