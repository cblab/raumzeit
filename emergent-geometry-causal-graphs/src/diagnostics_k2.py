from __future__ import annotations

import bisect
import math
from collections import deque

import numpy as np

from .graph_model import GraphState


def _build_shadow_adjacency(g: GraphState, region_nodes: list[int]) -> dict[int, set[int]]:
    region_set = set(region_nodes)
    neigh = {u: set() for u in region_nodes}
    for eid in g.active_edge_ids:
        i = g.src[eid]
        j = g.dst[eid]
        if i in region_set and j in region_set:
            neigh[i].add(j)
            neigh[j].add(i)
    return neigh


def _sample_bfs_region(g: GraphState, target_size: int) -> list[int]:
    if g.num_nodes == 0:
        return []

    start = int(g.rng.integers(0, g.num_nodes))
    q = deque([start])
    seen = {start}
    region = [start]

    while q and len(region) < target_size:
        u = q.popleft()
        nbrs = []
        for eid in g.out_edges[u]:
            if g.active[eid]:
                nbrs.append(g.dst[eid])
        for eid in g.in_edges[u]:
            if g.active[eid]:
                nbrs.append(g.src[eid])

        g.rng.shuffle(nbrs)
        for v in nbrs:
            if v not in seen and v < g.num_nodes:
                seen.add(v)
                q.append(v)
                region.append(v)
                if len(region) >= target_size:
                    break

    return region


def _estimate_return_probabilities(
    adj: dict[int, set[int]],
    taus: list[int],
    walkers: int,
    rng: np.random.Generator,
    start_nodes: list[int] | None = None,
) -> dict[str, float]:
    valid_nodes = [u for u, nbrs in adj.items() if len(nbrs) > 0]
    if start_nodes is None:
        allowed_starts = valid_nodes
    else:
        start_set = set(start_nodes)
        allowed_starts = [u for u in valid_nodes if u in start_set]

    if not allowed_starts:
        return {str(int(t)): 0.0 for t in taus}

    taus_sorted = sorted(int(t) for t in taus)
    tau_set = set(taus_sorted)
    max_tau = taus_sorted[-1]
    returns = {tau: 0 for tau in taus_sorted}

    starts = rng.choice(allowed_starts, size=max(1, walkers), replace=True)
    for start in starts:
        cur = int(start)
        for t in range(1, max_tau + 1):
            nbrs = tuple(adj[cur])
            if not nbrs:
                break
            cur = nbrs[int(rng.integers(0, len(nbrs)))]
            if t in tau_set and cur == start:
                returns[t] += 1

    return {str(t): returns[t] / max(1, walkers) for t in taus_sorted}


def _estimate_spectral_dimension(return_probs: dict[str, float]) -> float | None:
    taus = sorted(int(k) for k in return_probs.keys())
    ds_pairs = []
    for a, b in zip(taus[:-1], taus[1:]):
        pa = return_probs.get(str(a), 0.0)
        pb = return_probs.get(str(b), 0.0)
        if pa > 0.0 and pb > 0.0 and pb < pa:
            ds = -2.0 * math.log(pb / pa) / math.log(b / a)
            ds_pairs.append(ds)
    if not ds_pairs:
        return None
    return float(np.mean(ds_pairs))


def _estimate_volume_growth_dimension(adj: dict[int, set[int]], region_nodes: list[int], rng: np.random.Generator) -> float | None:
    if not region_nodes:
        return None

    center = int(rng.choice(region_nodes))
    q = deque([(center, 0)])
    dist = {center: 0}

    while q:
        u, d = q.popleft()
        for v in adj[u]:
            if v not in dist:
                dist[v] = d + 1
                q.append((v, d + 1))

    dvals = sorted(dist.values())
    if len(dvals) < 10:
        return None

    radii = [2, 3, 4, 5, 6]
    radii = [r for r in radii if bisect.bisect_right(dvals, r) > 10]
    if len(radii) < 2:
        return None

    logs_r = []
    logs_v = []
    for r in radii:
        vol = bisect.bisect_right(dvals, r)
        if vol > 0:
            logs_r.append(math.log(r))
            logs_v.append(math.log(vol))

    if len(logs_r) < 2:
        return None

    slope = np.polyfit(logs_r, logs_v, 1)[0]
    return float(slope)


def measure_k2_global(g: GraphState, config: dict) -> dict:
    region_size = int(config.get("k2_region_size", 1500))
    taus = [int(t) for t in config.get("k2_taus", [2, 4, 8, 16])]
    walkers = int(config.get("k2_walkers", 800))

    region_nodes = _sample_bfs_region(g, target_size=region_size)
    if len(region_nodes) < 2:
        return {
            "num_region_nodes": 0,
            "region_fraction": 0.0,
            "shadow_mean_degree": 0.0,
            "return_probs": {str(t): 0.0 for t in taus},
            "ds_est": None,
            "dv_est": None,
            "spectral_dimension_ds": None,
            "volume_growth_dimension_dv": None,
        }

    shadow_adj = _build_shadow_adjacency(g, region_nodes)
    mean_shadow_deg = float(np.mean([len(shadow_adj[u]) for u in region_nodes]))

    return_probs = _estimate_return_probabilities(shadow_adj, taus, walkers, g.rng)
    ds_est = _estimate_spectral_dimension(return_probs)
    dv_est = _estimate_volume_growth_dimension(shadow_adj, region_nodes, g.rng)

    return {
        "num_region_nodes": int(len(region_nodes)),
        "region_fraction": float(len(region_nodes) / max(1, g.num_nodes)),
        "shadow_mean_degree": mean_shadow_deg,
        "return_probs": {k: float(v) for k, v in return_probs.items()},
        "ds_est": float(ds_est) if ds_est is not None else None,
        "dv_est": float(dv_est) if dv_est is not None else None,
        "spectral_dimension_ds": float(ds_est) if ds_est is not None else None,
        "volume_growth_dimension_dv": float(dv_est) if dv_est is not None else None,
    }
