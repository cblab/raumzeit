from __future__ import annotations

import math

import numpy as np

from .diagnostics_k2 import _sample_bfs_region
from .diagnostics_k7 import _build_shadow_adjacency, shell_distribution_from_seed
from .graph_model import GraphState


def measure_k5_global(g: GraphState, config: dict) -> dict | None:
    region = _sample_bfs_region(g, int(config.get("k2_region_size", 1500)))
    if len(region) < 50:
        return None

    neigh = _build_shadow_adjacency(g, region)

    seed = int(g.rng.choice(region))
    shells, _ = shell_distribution_from_seed(neigh, seed)

    arr = np.array(shells, dtype=np.float64)
    total = arr.sum()
    if total <= 0:
        return None

    p = arr / total
    shell_entropy = float(-np.sum(p * np.log(p + 1e-12)))
    radii = np.arange(len(arr), dtype=np.float64)
    mean_r = float(np.sum(radii * p))
    var_r = float(np.sum(((radii - mean_r) ** 2) * p))
    front_thickness = math.sqrt(max(0.0, var_r))
    peak_shell = int(np.argmax(arr))

    return {
        "region_nodes": len(region),
        "region_fraction": len(region) / max(1, g.num_nodes),
        "shell_entropy": shell_entropy,
        "front_thickness": front_thickness,
        "peak_shell": peak_shell,
    }
