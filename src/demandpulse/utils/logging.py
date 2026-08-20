"""Structured logging configuration for production modules."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

DEFAULT_LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
_RESERVED = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    """Serialize log records as one-line JSON suitable for Cloud Logging ingestion."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key in _RESERVED or key.startswith("_"):
                continue
            if isinstance(value, (str, int, float, bool)) or value is None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))


def configure_logging(level: int | str = logging.INFO, *, json_output: bool = False) -> None:
    """Configure root logging once with JSON or human-readable output."""
    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(logging.StreamHandler(sys.stdout))
    formatter: logging.Formatter = JsonFormatter() if json_output else logging.Formatter(DEFAULT_LOG_FORMAT)
    for handler in root.handlers:
        handler.setFormatter(formatter)
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger without adding duplicate handlers."""
    return logging.getLogger(name)
