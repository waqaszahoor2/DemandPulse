"""Reference-vs-recent drift diagnostics."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp


def population_stability_index(
    reference: Sequence,
    recent: Sequence,
    *,
    bins: int = 10,
    epsilon: float = 1e-6,
) -> float:
    """PSI using reference-derived quantile bins for continuous features."""
    ref = pd.Series(reference)
    cur = pd.Series(recent)
    if bins < 2:
        raise ValueError("bins must be at least 2")
    if pd.api.types.is_numeric_dtype(ref) and ref.dropna().nunique() > bins:
        clean_ref = pd.to_numeric(ref, errors="coerce").dropna().to_numpy(dtype=float)
        if not len(clean_ref):
            return np.nan
        quantiles = np.unique(np.quantile(clean_ref, np.linspace(0, 1, bins + 1)))
        if len(quantiles) < 3:
            return 0.0
        edges = np.concatenate(([-np.inf], quantiles[1:-1], [np.inf]))
        ref_bins = pd.cut(pd.to_numeric(ref, errors="coerce"), edges, include_lowest=True).astype(str)
        cur_bins = pd.cut(pd.to_numeric(cur, errors="coerce"), edges, include_lowest=True).astype(str)
    else:
        ref_bins = ref.astype("object").where(ref.notna(), "__MISSING__").astype(str)
        cur_bins = cur.astype("object").where(cur.notna(), "__MISSING__").astype(str)
    ref_bins = ref_bins.where(ref.notna(), "__MISSING__")
    cur_bins = cur_bins.where(cur.notna(), "__MISSING__")
    categories = sorted(set(ref_bins.unique()) | set(cur_bins.unique()))
    ref_dist = ref_bins.value_counts(normalize=True).reindex(categories, fill_value=0.0).clip(lower=epsilon)
    cur_dist = cur_bins.value_counts(normalize=True).reindex(categories, fill_value=0.0).clip(lower=epsilon)
    return float(((cur_dist - ref_dist) * np.log(cur_dist / ref_dist)).sum())


def ks_statistic(reference: Sequence[float], recent: Sequence[float]) -> dict[str, float]:
    """Two-sample Kolmogorov-Smirnov statistic for numeric distributions."""
    ref = pd.to_numeric(pd.Series(reference), errors="coerce").dropna().to_numpy(dtype=float)
    cur = pd.to_numeric(pd.Series(recent), errors="coerce").dropna().to_numpy(dtype=float)
    if len(ref) < 2 or len(cur) < 2:
        return {"statistic": np.nan, "pvalue": np.nan}
    result = ks_2samp(ref, cur, alternative="two-sided", method="auto")
    return {"statistic": float(result.statistic), "pvalue": float(result.pvalue)}


def missing_value_drift(reference: pd.DataFrame, recent: pd.DataFrame) -> pd.DataFrame:
    """Compare missing rates for common columns."""
    columns = sorted(set(reference.columns) & set(recent.columns))
    rows = []
    for column in columns:
        ref_rate = float(reference[column].isna().mean())
        cur_rate = float(recent[column].isna().mean())
        rows.append(
            {
                "feature": column,
                "reference_missing_rate": ref_rate,
                "recent_missing_rate": cur_rate,
                "missing_rate_change": cur_rate - ref_rate,
            }
        )
    return pd.DataFrame(rows)


def category_drift(reference: Sequence, recent: Sequence) -> dict[str, float]:
    """Measure new-category rate and total-variation distance."""
    ref = pd.Series(reference).astype("object").where(pd.Series(reference).notna(), "__MISSING__").astype(str)
    cur = pd.Series(recent).astype("object").where(pd.Series(recent).notna(), "__MISSING__").astype(str)
    ref_categories = set(ref.unique())
    new_rate = float((~cur.isin(ref_categories)).mean()) if len(cur) else np.nan
    categories = sorted(ref_categories | set(cur.unique()))
    p = ref.value_counts(normalize=True).reindex(categories, fill_value=0.0)
    q = cur.value_counts(normalize=True).reindex(categories, fill_value=0.0)
    tv = 0.5 * float(np.abs(p - q).sum())
    return {"new_category_rate": new_rate, "total_variation": tv}
