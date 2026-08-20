"""Vercel Serverless Function Entrypoint for DemandPulse FastAPI API.

Exposes the core DemandPulse FastAPI application without duplicating route logic.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is on python path for Vercel serverless imports
root_dir = Path(__file__).resolve().parent.parent
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from demandpulse.api.main import app

__all__ = ["app"]
