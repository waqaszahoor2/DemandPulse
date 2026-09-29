#!/usr/bin/env python3
"""DemandPulse Deployment Validator for Vercel Release Readiness."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def validate_api_entrypoint() -> bool:
    print("\n1. Validating Vercel API Entrypoint (api/index.py)...")
    entrypoint = PROJECT_ROOT / "api" / "index.py"
    if not entrypoint.exists():
        print("[FAIL]: api/index.py does not exist.")
        return False
    try:
        from fastapi import FastAPI

        from api.index import app

        if not isinstance(app, FastAPI):
            print("[FAIL]: app exported from api/index.py is not a FastAPI instance.")
            return False
        print("   [OK] api/index.py successfully imports FastAPI app.")
        return True
    except Exception as exc:
        print(f"[FAIL] to import app from api/index.py: {exc}")
        return False


def validate_requirements() -> bool:
    print("\n2. Validating Requirements & Dependencies...")
    req = PROJECT_ROOT / "requirements.txt"
    if not req.exists():
        print("[FAIL]: requirements.txt does not exist.")
        return False
    content = req.read_text(encoding="utf-8")
    for dep in ["fastapi", "lightgbm", "pandas", "pydantic"]:
        if dep not in content:
            print(f"[FAIL]: {dep} missing from requirements.txt.")
            return False
    print("   [OK] Production requirements.txt validated.")
    return True


def validate_secret_safety() -> bool:
    print("\n3. Scanning for Exposed Secrets...")
    suspicious_terms = ["AKIA", "SECRET_KEY=", "AWS_SECRET", "PASSWORD="]
    for ext in [".py", ".json", ".yml", ".toml"]:
        for path in PROJECT_ROOT.glob(f"**/*{ext}"):
            if "venv" in str(path) or ".git" in str(path):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
                for term in suspicious_terms:
                    if term in text and not path.name.endswith(".example"):
                        print(f"[WARN]: Potential secret '{term}' found in {path}")
                        return False
            except Exception:
                pass
    print("   [OK] No obvious committed secrets found.")
    return True


def validate_notebook_execution_report() -> bool:
    print("\n4. Validating Notebook Execution Audit Report...")
    report_file = PROJECT_ROOT / "reports" / "notebook_execution_report.json"
    if not report_file.exists():
        print(
            "[FAIL]: reports/notebook_execution_report.json does not exist. Run scripts/run_all_notebooks.py first."
        )
        return False
    try:
        with open(report_file, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list) or len(data) < 7:
            print(
                f"[FAIL]: Execution report contains {len(data) if isinstance(data, list) else 0} entries; expected 7."
            )
            return False

        failed = [item for item in data if item.get("status") != "PASS"]
        if failed:
            print("[FAIL]: The following notebooks failed during execution pipeline:")
            for item in failed:
                print(f" - {item['notebook']}: {item.get('error')}")
            return False

        print(f"   [OK] All {len(data)} research notebooks reported PASS status.")
        return True
    except Exception as exc:
        print(f"[FAIL] to parse notebook execution report: {exc}")
        return False


def validate_models_and_config() -> bool:
    print("\n5. Validating Environment Variables & Config...")
    env_example = PROJECT_ROOT / ".env.example"
    if not env_example.exists():
        print("[FAIL]: .env.example does not exist.")
        return False
    content = env_example.read_text(encoding="utf-8")
    required_vars = ["APP_ENV", "LOG_LEVEL", "MODEL_DIR"]
    for var in required_vars:
        if var not in content:
            print(f"[FAIL]: {var} missing from .env.example.")
            return False
    print("   [OK] Environment configuration documented.")
    return True


def main() -> int:
    print("=" * 70)
    print("DemandPulse Vercel Deployment Validator")
    print("=" * 70)

    checks = [
        validate_api_entrypoint(),
        validate_requirements(),
        validate_secret_safety(),
        validate_notebook_execution_report(),
        validate_models_and_config(),
    ]

    print("=" * 70)
    if all(checks):
        print("ALL DEPLOYMENT VALIDATION CHECKS PASSED!")
        return 0
    else:
        print("DEPLOYMENT VALIDATION FAILED. RESOLVE ISSUES ABOVE BEFORE RELEASE.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
