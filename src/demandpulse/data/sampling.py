"""Deterministic complete-series sampling."""

from __future__ import annotations

import hashlib
from collections.abc import MutableMapping
from typing import Any


def series_bucket(store_id: Any, product_id: Any, buckets: int = 10_000) -> int:
    """Return the stable SHA-256 bucket used by the DemandPulse notebooks."""
    if buckets <= 0:
        raise ValueError("buckets must be positive")
    token = f"{store_id}-{product_id}".encode("utf-8")
    digest = hashlib.sha256(token).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False) % buckets


def series_selected(
    store_id: Any,
    product_id: Any,
    percent: float = 30.0,
    cache: MutableMapping[tuple[Any, Any], bool] | None = None,
) -> bool:
    """Select a complete store-product series using the research SHA-256 rule.

    The 10,000 buckets provide 0.01 percentage-point resolution. The same
    store/product pair always receives the same decision in train and eval.
    """
    if not 0.0 <= percent <= 100.0:
        raise ValueError("percent must be between 0 and 100")
    if percent >= 100.0:
        return True
    if percent <= 0.0:
        return False

    key = (store_id, product_id)
    if cache is not None and key in cache:
        return cache[key]

    selected = series_bucket(store_id, product_id) < int(round(percent * 100))
    if cache is not None:
        cache[key] = selected
    return selected
