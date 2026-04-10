from __future__ import annotations

from collections import deque

import numpy as np

from .graph_model import GraphState, active_undirected_neighbors



def _sample_bfs_region(g: GraphState, target_size: int) -> list[int]:
    if g.num_nodes <= 0:
        return []

    start = int(g.rng.integers(0, g.num_nodes))
    visited: set[int] = {start}
    queue: deque[int] = deque([start])

    while queue and len(visited) < target_size:
        u = queue.popleft()
        for v in active_undirected_neighbors(g, u):
            if v in visited:
                continue
            visited.add(v)
            queue.append(v)
            if len(visited) >= target_size:
                break

    if len(visited) < min(target_size, g.num_nodes):
        candidates = np.arange(g.num_nodes)
        perm = g.rng.permutation(candidates)
        for node in perm:
            node_i = int(node)
            if node_i not in visited:
                visited.add(node_i)
            if len(visited) >= min(target_size, g.num_nodes):
                break

    return sorted(visited)



def _shadow_adjacency_for_region(g: GraphState, region_nodes: list[int]) -> dict[int, list[int]]:
    region_set = set(region_nodes)
    adj: dict[int, list[int]] = {u: [] for u in region_nodes}

    for u in region_nodes:
        nbrs = [v for v in active_undirected_neighbors(g, u) if v in region_set]
        adj[u] = sorted(set(nbrs))

    return adj



def _estimate_return_probabilities(
    adj: dict[int, list[int]], taus: list[int], walkers: int, rng: np.random.Generator
) -> dict[str, float]:
    if not adj:
        return {str(int(t)): 0.0 for t in taus}

    nodes = list(adj.keys())
    probs: dict[str, float] = {}

    for tau in taus:
        tau_i = int(tau)
        if tau_i <= 0:
            probs[str(tau_i)] = 1.0
            continue

        returns = 0
        for _ in range(max(1, walkers)):
            start = int(nodes[int(rng.integers(0, len(nodes)))])
            cur = start
            for _ in range(tau_i):
                nbrs = adj.get(cur, [])
                if not nbrs:
                    break
                cur = int(nbrs[int(rng.integers(0, len(nbrs)))])
            if cur == start:
                returns += 1

        probs[str(tau_i)] = float(returns / max(1, walkers))

    return probs



def _estimate_spectral_dimension(return_probs: dict[str, float]) -> float | None:
    xs = []
    ys = []
    for tau_s, p in return_probs.items():
        tau = int(tau_s)
        if tau > 0 and p > 0.0:
            xs.append(np.log(float(tau)))
            ys.append(np.log(float(p)))

    if len(xs) < 2:
        return None

    slope, _ = np.polyfit(np.array(xs), np.array(ys), 1)
    return float(-2.0 * slope)



def _estimate_volume_growth_dimension(adj: dict[int, list[int]], root: int) -> float | None:
    if root not in adj:
        return None

    dist = {root: 0}
    queue: deque[int] = deque([root])

    while queue:
        u = queue.popleft()
        for v in adj.get(u, []):
            if v in dist:
                continue
            dist[v] = dist[u] + 1
            queue.append(v)

    if len(dist) < 3:
        return None

    max_r = max(dist.values())
    radii = []
    volumes = []
    for r in range(1, max_r + 1):
        v_r = sum(1 for d in dist.values() if d <= r)
        if v_r > 1:
            radii.append(np.log(float(r)))
            volumes.append(np.log(float(v_r)))

    if len(radii) < 2:
        return None

    slope, _ = np.polyfit(np.array(radii), np.array(volumes), 1)
    return float(slope)



def measure_k2_global(g: GraphState, config: dict) -> dict:
    region_size = int(config.get("k2_region_size", 256))
    taus = [int(t) for t in config.get("k2_taus", [1, 2, 4, 8, 16])]
    walkers = int(config.get("k2_walkers", 256))

    region_nodes = _sample_bfs_region(g, target_size=max(1, region_size))
    shadow_adj = _shadow_adjacency_for_region(g, region_nodes)

    return_probs = _estimate_return_probabilities(shadow_adj, taus, walkers, g.rng)
    ds_est = _estimate_spectral_dimension(return_probs)
    dv_est = _estimate_volume_growth_dimension(shadow_adj, root=region_nodes[0]) if region_nodes else None

    sampled_edges = sum(len(v) for v in shadow_adj.values()) // 2

    return {
        "region_size": int(len(region_nodes)),
        "region_nodes": [int(n) for n in region_nodes],
        "sampled_shadow_edges": int(sampled_edges),
        "taus": [int(t) for t in taus],
        "return_probabilities": {k: float(v) for k, v in return_probs.items()},
        "spectral_dimension_ds": float(ds_est) if ds_est is not None else None,
        "volume_growth_dimension_dv": float(dv_est) if dv_est is not None else None,
    }
