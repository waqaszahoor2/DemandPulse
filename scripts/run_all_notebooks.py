#!/usr/bin/env python3
"""Sequential notebook execution and audit script for DemandPulse.

Discovers research notebooks 01 through 07, executes them in fresh kernels
with configurable timeouts, preserves outputs, saves executed copies under
notebooks/executed/, and generates reports/notebook_execution_report.json.
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
EXECUTED_DIR = NOTEBOOKS_DIR / "executed"
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORT_FILE = REPORTS_DIR / "notebook_execution_report.json"

DEFAULT_TIMEOUT = int(os.environ.get("NOTEBOOK_TIMEOUT", "7200"))


def discover_notebooks() -> list[Path]:
    """Find notebooks 01 through 07 in notebooks directory."""
    if not NOTEBOOKS_DIR.exists():
        raise FileNotFoundError(f"Notebooks directory not found: {NOTEBOOKS_DIR}")

    prefix_map: dict[str, Path | None] = {
        "01": None,
        "02": None,
        "03": None,
        "04": None,
        "05": None,
        "06": None,
        "07": None,
    }

    for path in sorted(NOTEBOOKS_DIR.glob("*.ipynb")):
        if path.parent == EXECUTED_DIR:
            continue
        prefix = path.name[:2]
        if prefix in prefix_map and prefix_map[prefix] is None:
            prefix_map[prefix] = path

    missing = [prefix for prefix, path in prefix_map.items() if path is None]
    if missing:
        raise FileNotFoundError(f"Missing required notebooks for prefixes: {missing} in {NOTEBOOKS_DIR}")

    return [prefix_map[prefix] for prefix in sorted(prefix_map.keys())]  # type: ignore[misc]


def execute_single_notebook(notebook_path: Path, timeout: int) -> dict[str, Any]:
    """Execute a single notebook in a fresh kernel and save output."""
    print(f"\n{'=' * 70}")
    print(f">> Executing: {notebook_path.name}")
    print(f"   Timeout: {timeout} seconds")
    print(f"{'=' * 70}")

    start_time = time.time()
    EXECUTED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = EXECUTED_DIR / notebook_path.name

    with open(notebook_path, encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    client = NotebookClient(
        nb,
        timeout=timeout,
        kernel_name="python3",
        allow_errors=False,
        resources={"metadata": {"path": str(PROJECT_ROOT)}},
    )

    error_info: dict[str, Any] | None = None
    status = "PASS"

    try:
        client.execute()
    except CellExecutionError as exc:
        status = "FAIL"
        cell_index = getattr(exc, "cell_index", -1)
        ename = getattr(exc, "ename", "CellExecutionError")
        evalue = getattr(exc, "evalue", str(exc))
        error_info = {
            "cell_index": cell_index,
            "ename": ename,
            "evalue": evalue,
            "traceback": getattr(exc, "traceback", [str(exc)]),
        }
        print(f"\n[FAILED]: {notebook_path.name} at Cell #{cell_index}")
        print(f"   Exception: {ename}: {evalue}")
        print("-" * 50)
        for tb_line in getattr(exc, "traceback", []):
            print(tb_line)
        print("-" * 50)
    except Exception as exc:
        status = "FAIL"
        error_info = {
            "cell_index": -1,
            "ename": type(exc).__name__,
            "evalue": str(exc),
            "traceback": [traceback.format_exc()],
        }
        print(f"\n[FAILED]: {notebook_path.name} with unexpected error:")
        print(f"   {exc}")

    # Save executed notebook with cell outputs intact
    with open(out_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)

    elapsed_time = round(time.time() - start_time, 2)
    output_cells = sum(1 for c in nb.cells if c.cell_type == "code" and c.outputs)

    print(f"[SAVED]: Executed notebook saved to {out_path}")
    print(f"   Status: {status} | Duration: {elapsed_time}s | Code Output Cells: {output_cells}")

    return {
        "notebook": notebook_path.name,
        "status": status,
        "execution_time": elapsed_time,
        "output_cells": output_cells,
        "error": error_info,
    }


def main() -> int:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    notebooks = discover_notebooks()
    report: list[dict[str, Any]] = []

    print("DemandPulse Notebook Pipeline Execution")
    print(f"Discovered {len(notebooks)} notebooks:")
    for nb in notebooks:
        print(f" - {nb.name}")

    overall_passed = True
    for nb_path in notebooks:
        result = execute_single_notebook(nb_path, DEFAULT_TIMEOUT)
        report.append(result)

        if result["status"] != "PASS":
            overall_passed = False
            print(f"\n[HALTED]: Execution pipeline halted immediately due to failure in {nb_path.name}.")
            break

    # Save execution audit report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n{'=' * 70}")
    print(f"Execution Report Saved: {REPORT_FILE}")
    print(f"{'=' * 70}")

    for item in report:
        st = "[PASS]" if item["status"] == "PASS" else "[FAIL]"
        print(
            f" {st} | {item['notebook']:<45} | {item['execution_time']:>6.2f}s | {item['output_cells']} outputs"
        )

    if overall_passed:
        print("\nALL 7 DEMANDPULSE NOTEBOOKS EXECUTED AND PASSED SUCCESSFULLY!")
        return 0
    else:
        print("\nNOTEBOOK PIPELINE FAILED. SEE ERROR DETAILS ABOVE.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
