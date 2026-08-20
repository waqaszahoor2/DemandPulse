"""FastAPI serving layer for DemandPulse."""

from demandpulse.api.main import app, create_app

__all__ = ["app", "create_app"]
