#!/usr/bin/env python3
"""Audit model artifact file sizes for serverless deployment budget."""

from __future__ import annotations

import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
OUTPUT_CSV = REPORTS_DIR / "model_size_audit.csv"

# Models required for live serving vs offline research
REQUIRED_API_PATTERNS = [
    "demandpulse_lgbm.txt",
    "quantile",
]


def is_required_for_api(path: Path) -> bool:
    rel = str(path.relative_to(MODELS_DIR))
    for pat in REQUIRED_API_PATTERNS:
        if pat in rel:
            return True
    return False


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    total_mb = 0.0

    for path in sorted(MODELS_DIR.rglob("*")):
        if path.is_file() and not path.name.startswith("."):
            size_mb = round(path.stat().st_size / (1024 * 1024), 4)
            rel_path = str(path.relative_to(PROJECT_ROOT))
            req = is_required_for_api(path)
            rows.append({
                "model": path.name,
                "path": rel_path,
                "size_mb": size_mb,
                "required_for_api": req,
            })
            total_mb += size_mb

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["model", "path", "size_mb", "required_for_api"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Model size audit complete: {OUTPUT_CSV}")
    print(f"Total model footprint: {round(total_mb, 2)} MB ({len(rows)} files)")
    for r in rows:
        print(f" - {r['model']:<35} | {r['size_mb']:>7.3f} MB | Required: {r['required_for_api']}")


if __name__ == "__main__":
    main()
