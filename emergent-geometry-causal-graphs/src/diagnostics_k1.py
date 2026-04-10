from __future__ import annotations

import numpy as np

from .graph_model import GraphState, active_undirected_neighbors, active_weights_np, shared_neighbor_fraction_from_sets


def measure_k1(g: GraphState, config: dict | None = None) -> dict:
    """
    K1: first-order structural coherence proxy.

    Returns a compact dict that is stable enough to store per-step in run histories.
    """

    if g.num_nodes == 0:
        return {
            "k1": 0.0,
            "num_nodes": 0,
            "active_edges": 0,
            "mean_weight": 0.0,
            "weight_std": 0.0,
            "mean_shadow_degree": 0.0,
            "max_level": 0,
        }

    sample_limit = int((config or {}).get("k1_edge_sample", 4096))

    weights = active_weights_np(g)
    mean_w = float(np.mean(weights)) if weights.size else 0.0
    std_w = float(np.std(weights)) if weights.size else 0.0

    n = g.num_nodes
    shadow_degs = np.zeros(n, dtype=np.float64)
    for u in range(n):
        shadow_degs[u] = len(active_undirected_neighbors(g, u))
    mean_shadow = float(np.mean(shadow_degs)) if n else 0.0

    edge_ids = g.active_edge_ids
    if len(edge_ids) > sample_limit:
        edge_ids = g.rng.choice(edge_ids, size=sample_limit, replace=False).tolist()

    overlap_vals = []
    for eid in edge_ids:
        i = g.src[eid]
        j = g.dst[eid]
        ni = active_undirected_neighbors(g, i)
        nj = active_undirected_neighbors(g, j)
        overlap_vals.append(shared_neighbor_fraction_from_sets(ni, nj))

    k1_val = float(np.mean(overlap_vals)) if overlap_vals else 0.0

    return {
        "k1": k1_val,
        "num_nodes": int(g.num_nodes),
        "active_edges": int(g.active_edge_count),
        "mean_weight": mean_w,
        "weight_std": std_w,
        "mean_shadow_degree": mean_shadow,
        "max_level": int(g.current_max_level),
    }
