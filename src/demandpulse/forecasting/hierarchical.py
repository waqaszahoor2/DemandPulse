"""Hierarchy construction and forecast reconciliation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import LinearOperator, cg


@dataclass(frozen=True)
class HierarchyMatrix:
    """Sparse summing matrix plus node and bottom-series metadata."""

    matrix: csr_matrix
    nodes: pd.DataFrame
    bottom: pd.DataFrame


def _node_labels(bottom: pd.DataFrame) -> pd.DataFrame:
    out = bottom.copy()
    out["company_node"] = "Company"
    out["city_node"] = "City:" + out["city_id"].astype(str)
    out["store_node"] = "Store:" + out["store_id"].astype(str)
    out["category_node"] = (
        "Category:" + out["store_id"].astype(str) + ":" + out["third_category_id"].astype(str)
    )
    out["product_node"] = (
        "Product:" + out["store_id"].astype(str) + ":" + out["product_id"].astype(str)
    )
    return out


def build_summing_matrix(mapping: pd.DataFrame) -> HierarchyMatrix:
    """Build Company→City→Store→store-local Category→Product summing matrix."""
    required = {"city_id", "store_id", "third_category_id", "product_id"}
    missing = sorted(required - set(mapping.columns))
    if missing:
        raise KeyError(f"Hierarchy mapping is missing: {missing}")
    bottom = mapping[list(required)].drop_duplicates().reset_index(drop=True)
    bottom = _node_labels(bottom)

    # A store must belong to one city for a strict tree.
    city_per_store = bottom.groupby("store_id", observed=True)["city_id"].nunique()
    if (city_per_store > 1).any():
        bad = city_per_store[city_per_store > 1].index.tolist()[:10]
        raise ValueError(f"Stores mapped to multiple cities: {bad}")

    ordered_nodes: list[tuple[str, str]] = [("Company", "Company")]
    for level, column in [
        ("City", "city_node"),
        ("Store", "store_node"),
        ("Category", "category_node"),
        ("Product", "product_node"),
    ]:
        ordered_nodes.extend((node, level) for node in sorted(bottom[column].unique()))
    nodes = pd.DataFrame(ordered_nodes, columns=["node_id", "level"])
    nodes["row_idx"] = np.arange(len(nodes))
    node_index = dict(zip(nodes["node_id"], nodes["row_idx"]))

    rows: list[int] = []
    cols: list[int] = []
    values: list[float] = []
    for bottom_col, row in bottom.iterrows():
        ancestors = [
            row["company_node"],
            row["city_node"],
            row["store_node"],
            row["category_node"],
            row["product_node"],
        ]
        for node in ancestors:
            rows.append(node_index[node])
            cols.append(bottom_col)
            values.append(1.0)

    matrix = csr_matrix((values, (rows, cols)), shape=(len(nodes), len(bottom)), dtype=float)
    bottom["bottom_col"] = np.arange(len(bottom))
    return HierarchyMatrix(matrix=matrix, nodes=nodes, bottom=bottom)


def bottom_up_reconciliation(base_forecasts: np.ndarray, hierarchy: HierarchyMatrix) -> np.ndarray:
    """Use independent Product forecasts as the bottom vector and aggregate upward."""
    base = np.asarray(base_forecasts, dtype=float)
    if len(base) != hierarchy.matrix.shape[0]:
        raise ValueError("base_forecasts length does not match hierarchy rows")
    node_index = dict(zip(hierarchy.nodes["node_id"], hierarchy.nodes["row_idx"]))
    bottom = np.asarray(
        [base[node_index[node]] for node in hierarchy.bottom["product_node"]],
        dtype=float,
    )
    return np.asarray(hierarchy.matrix @ bottom).ravel()


def top_down_reconciliation(
    base_forecasts: np.ndarray,
    hierarchy: HierarchyMatrix,
    bottom_shares: np.ndarray,
) -> np.ndarray:
    """Allocate the Company forecast to products using historical bottom shares."""
    base = np.asarray(base_forecasts, dtype=float)
    shares = np.asarray(bottom_shares, dtype=float)
    if len(shares) != hierarchy.matrix.shape[1]:
        raise ValueError("bottom_shares length does not match number of products")
    if np.any(shares < 0) or shares.sum() <= 0:
        raise ValueError("bottom_shares must be non-negative with positive sum")
    shares = shares / shares.sum()
    company_row = int(hierarchy.nodes.loc[hierarchy.nodes["level"].eq("Company"), "row_idx"].iloc[0])
    bottom = base[company_row] * shares
    return np.asarray(hierarchy.matrix @ bottom).ravel()


def middle_out_reconciliation(
    base_forecasts: np.ndarray,
    hierarchy: HierarchyMatrix,
    within_store_shares: np.ndarray,
) -> np.ndarray:
    """Use independent Store forecasts and allocate them to products within each store."""
    base = np.asarray(base_forecasts, dtype=float)
    shares = np.asarray(within_store_shares, dtype=float)
    if len(shares) != len(hierarchy.bottom):
        raise ValueError("within_store_shares length mismatch")
    if np.any(shares < 0):
        raise ValueError("within_store_shares must be non-negative")

    node_index = dict(zip(hierarchy.nodes["node_id"], hierarchy.nodes["row_idx"]))
    bottom = np.zeros(len(hierarchy.bottom), dtype=float)
    for store_node, group in hierarchy.bottom.groupby("store_node", sort=False):
        idx = group["bottom_col"].to_numpy(dtype=int)
        local = shares[idx]
        if local.sum() <= 0:
            local = np.full(len(idx), 1.0 / len(idx))
        else:
            local = local / local.sum()
        bottom[idx] = base[node_index[store_node]] * local
    return np.asarray(hierarchy.matrix @ bottom).ravel()


def mint_reconciliation(
    base_forecasts: np.ndarray,
    hierarchy: HierarchyMatrix,
    error_variances: np.ndarray,
    *,
    ridge: float = 1e-6,
    clip_bottom_nonnegative: bool = True,
) -> np.ndarray:
    """Diagonal-W MinT-style reconciliation solved in sparse bottom space."""
    base = np.asarray(base_forecasts, dtype=float)
    variances = np.asarray(error_variances, dtype=float)
    S = hierarchy.matrix
    if len(base) != S.shape[0] or len(variances) != S.shape[0]:
        raise ValueError("base/error_variance vectors must match hierarchy rows")
    if ridge < 0:
        raise ValueError("ridge must be non-negative")
    w_inv = 1.0 / np.maximum(variances, 1e-8)

    def matvec(vector: np.ndarray) -> np.ndarray:
        projected = np.asarray(S @ vector).ravel()
        return np.asarray(S.T @ (w_inv * projected)).ravel() + ridge * vector

    operator = LinearOperator((S.shape[1], S.shape[1]), matvec=matvec, dtype=float)
    rhs = np.asarray(S.T @ (w_inv * base)).ravel()
    bottom, info = cg(operator, rhs, atol=0.0, rtol=1e-6, maxiter=2_000)
    if info != 0:
        raise RuntimeError(f"MinT-style solver did not converge; info={info}")
    if clip_bottom_nonnegative:
        bottom = np.maximum(bottom, 0.0)
    return np.asarray(S @ bottom).ravel()


def coherence_error(forecasts: np.ndarray, hierarchy: HierarchyMatrix) -> float:
    """Measure distance from the coherent subspace using Bottom-Up projection."""
    base = np.asarray(forecasts, dtype=float)
    coherent = bottom_up_reconciliation(base, hierarchy)
    denom = np.abs(coherent).sum()
    return float(np.abs(base - coherent).sum() / denom) if denom > 0 else np.nan
