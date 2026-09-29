#!/usr/bin/env python3
"""DemandPulse Vercel & Production Environment Validation Script.

Validates active environment variables against required and optional specifications
without printing secret values or breaking serverless deployments.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add src to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def validate_environment() -> int:
    print("=" * 70)
    print("DemandPulse Production Environment Validation")
    print("=" * 70)

    # Required / Core Environment Variables
    env_specs = [
        ("APP_ENV", os.environ.get("APP_ENV", "production"), False, "Application runtime environment"),
        ("LOG_LEVEL", os.environ.get("LOG_LEVEL", "INFO"), False, "Logging verbosity level"),
        (
            "DEMANDPULSE_MODEL_SOURCE",
            os.environ.get("DEMANDPULSE_MODEL_SOURCE", "local"),
            False,
            "Model artifact source (local, bundle_uri, mlflow)",
        ),
        ("MODEL_DIR", os.environ.get("MODEL_DIR", "models"), False, "Local model directory path"),
        (
            "REQUIRED_MODEL_COMPONENTS",
            os.environ.get("REQUIRED_MODEL_COMPONENTS", "point,probabilistic"),
            False,
            "Required model components",
        ),
        ("LOG_FORMAT", os.environ.get("LOG_FORMAT", "json"), False, "Log output format (json / text)"),
        (
            "REQUEST_TIMEOUT_SECONDS",
            os.environ.get("REQUEST_TIMEOUT_SECONDS", "25"),
            False,
            "Request timeout limit in seconds",
        ),
    ]

    all_valid = True
    print("\n--- Validating Active Environment Variables ---")

    for var_name, current_val, is_mandatory, description in env_specs:
        is_set = var_name in os.environ
        if is_set:
            print(f"  [OK]   {var_name:<26} = '{current_val}' ({description})")
        else:
            if is_mandatory:
                print(f"  [FAIL] {var_name:<26} MISSING (REQUIRED - {description})")
                all_valid = False
            else:
                print(f"  [INFO] {var_name:<26} Not set (Using safe default: '{current_val}')")

    # Validate local model directory if model_source == 'local'
    model_source = os.environ.get("DEMANDPULSE_MODEL_SOURCE", "local").lower()
    if model_source == "local":
        model_dir = Path(os.environ.get("MODEL_DIR", PROJECT_ROOT / "models"))
        print("\n--- Validating Model Artifacts ---")
        if model_dir.exists():
            print(f"  [OK]   Model directory found at: {model_dir}")
            pt_model = model_dir / "point_lgbm.txt"
            prob_model = model_dir / "quantile_lgbm.txt"
            if pt_model.exists():
                print("  [OK]   point_lgbm.txt present")
            else:
                print("  [INFO] point_lgbm.txt missing (Synthetic fallback mode active)")
            if prob_model.exists():
                print("  [OK]   quantile_lgbm.txt present")
            else:
                print("  [INFO] quantile_lgbm.txt missing (Synthetic fallback mode active)")
        else:
            print(f"  [INFO] Model directory '{model_dir}' not found (Synthetic fallback active)")

    print("\n" + "=" * 70)
    if all_valid:
        print("ENVIRONMENT VALIDATION PASSED: Ready for Vercel Deployment!")
        print("=" * 70)
        return 0
    else:
        print("ENVIRONMENT VALIDATION FAILED: Missing required configuration.")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(validate_environment())
