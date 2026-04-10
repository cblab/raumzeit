from __future__ import annotations

from collections import Counter
import math

import numpy as np

from .graph_model import GraphState, active_weights_np


def measure_k1(g: GraphState, config: dict | None = None) -> dict:
    ws = active_weights_np(g)
    if ws.size == 0:
        return {
            "k1": 0.0,
            "num_nodes": int(g.num_nodes),
            "active_edges": int(g.active_edge_count),
            "num_edges_total": int(len(g.src)),
            "num_edges_active": int(g.active_edge_count),
            "mean_weight": 0.0,
            "std_weight": 0.0,
            "min_weight": 0.0,
            "max_weight": 0.0,
            "frac_near_wmin": 0.0,
            "frac_near_wmax": 0.0,
            "mean_k_out": 0.0,
            "var_k_out": 0.0,
            "H_degree": 0.0,
            "max_level": int(g.current_max_level),
        }

    w_min = float((config or {}).get("w_min", 0.10))
    w_max = float((config or {}).get("w_max", 3.0))

    deg = g.active_out_degree[: g.num_nodes].astype(np.float64)
    mean_k = float(np.mean(deg))
    var_k = float(np.var(deg))

    counts = Counter(deg.astype(int))
    probs = np.array(list(counts.values()), dtype=np.float64)
    probs = probs / probs.sum()
    h_deg = float(-np.sum(probs * np.log(probs + 1e-12)) / math.log(len(probs) + 1e-12))

    out = {
        "k1": h_deg,
        "num_nodes": int(g.num_nodes),
        "active_edges": int(g.active_edge_count),
        "num_edges_total": int(len(g.src)),
        "num_edges_active": int(g.active_edge_count),
        "mean_weight": float(np.mean(ws)),
        "std_weight": float(np.std(ws)),
        "min_weight": float(np.min(ws)),
        "max_weight": float(np.max(ws)),
        "frac_near_wmin": float(np.mean(ws <= (w_min + 0.05))),
        "frac_near_wmax": float(np.mean(ws >= (w_max - 0.10))),
        "mean_k_out": mean_k,
        "var_k_out": var_k,
        "H_degree": h_deg,
        "max_level": int(g.current_max_level),
    }
    return out
