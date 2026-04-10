from __future__ import annotations

import numpy as np

from .diagnostics_k2 import _sample_bfs_region
from .diagnostics_k7 import _build_shadow_adjacency
from .updates import ancestry_signature, jaccard_sets
from .graph_model import GraphState


def _bfs_distance(neigh, start, goal):
    if start == goal:
        return 0
    q = [start]
    dist = {start: 0}
    while q:
        u = q.pop(0)
        du = dist[u]
        for v in neigh[u]:
            if v == goal:
                return du + 1
            if v not in dist:
                dist[v] = du + 1
                q.append(v)
    return None


def measure_k4_global(g: GraphState, config: dict) -> dict | None:
    region = _sample_bfs_region(g, int(config.get("k2_region_size", 1500)))
    if len(region) < 50:
        return None

    neigh = _build_shadow_adjacency(g, region)

    herf_vals = []
    for j in region:
        incoming = [pe for pe in g.in_edges[j] if g.active[pe]]
        if len(incoming) <= 1:
            continue
        ws = np.array([g.w[pe] for pe in incoming], dtype=np.float64)
        s = ws.sum()
        if s <= 0:
            continue
        p = ws / s
        herf_vals.append(float(np.sum(p * p)))

    mean_herf = float(np.mean(herf_vals)) if herf_vals else None
    q90_herf = float(np.quantile(herf_vals, 0.9)) if herf_vals else None

    cluster_doms = []
    cross_sim_threshold = float(config.get("cross_sim_threshold", 0.35))
    for j in region:
        incoming = [pe for pe in g.in_edges[j] if g.active[pe]]
        m = len(incoming)
        if m <= 1:
            continue
        parent_nodes = [g.src[pe] for pe in incoming]
        sigs = [ancestry_signature(g, u, config) for u in parent_nodes]
        cluster_load = np.zeros(m, dtype=np.float64)

        for a in range(m):
            for b in range(a + 1, m):
                sim = jaccard_sets(sigs[a], sigs[b])
                if sim >= cross_sim_threshold:
                    excess = (sim - cross_sim_threshold) / (1.0 - cross_sim_threshold + 1e-12)
                    cluster_load[a] += excess * g.w[incoming[b]]
                    cluster_load[b] += excess * g.w[incoming[a]]

        total = float(cluster_load.sum())
        if total > 1e-12:
            p = cluster_load / total
            cluster_doms.append(float(np.max(p)))

    mean_cluster_dom = float(np.mean(cluster_doms)) if cluster_doms else None
    q90_cluster_dom = float(np.quantile(cluster_doms, 0.9)) if cluster_doms else None

    valid_nodes = [u for u in region if len(neigh[u]) > 0]
    effs = []
    dists = []

    if len(valid_nodes) >= 2:
        pair_count = min(int(config.get("k4_pair_samples", 300)), len(valid_nodes) * (len(valid_nodes) - 1) // 2)
        for _ in range(pair_count):
            a, b = g.rng.choice(valid_nodes, size=2, replace=False)
            d = _bfs_distance(neigh, int(a), int(b))
            if d is None:
                effs.append(0.0)
            else:
                dists.append(d)
                effs.append(1.0 / d if d > 0 else 0.0)

    return {
        "region_nodes": len(region),
        "region_fraction": len(region) / max(1, g.num_nodes),
        "mean_in_herfindahl": mean_herf,
        "q90_in_herfindahl": q90_herf,
        "mean_cluster_dominance": mean_cluster_dom,
        "q90_cluster_dominance": q90_cluster_dom,
        "mean_global_efficiency": float(np.mean(effs)) if effs else None,
        "mean_sample_path_length": float(np.mean(dists)) if dists else None,
    }
