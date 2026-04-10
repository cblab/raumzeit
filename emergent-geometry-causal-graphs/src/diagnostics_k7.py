from __future__ import annotations

from collections import deque

import numpy as np

from .diagnostics_k2 import (
    _estimate_return_probabilities,
    _estimate_spectral_dimension,
    _estimate_volume_growth_dimension,
)
from .graph_model import GraphState, active_undirected_neighbors


def sample_bfs_region_from_seed(g: GraphState, seed: int, target_size: int) -> list[int]:
    """Grow a region from a fixed seed using BFS over active shadow edges."""
    if g.num_nodes <= 0:
        return []

    seed_i = int(seed)
    if seed_i < 0 or seed_i >= g.num_nodes:
        return []

    target = max(1, min(int(target_size), int(g.num_nodes)))
    visited: set[int] = {seed_i}
    queue: deque[int] = deque([seed_i])

    while queue and len(visited) < target:
        u = queue.popleft()
        for v in sorted(active_undirected_neighbors(g, u)):
            if v in visited:
                continue
            visited.add(int(v))
            queue.append(int(v))
            if len(visited) >= target:
                break

    return sorted(visited)


def initialize_anchors(g: GraphState, config: dict) -> list[dict]:
    """Initialize fixed anchors once using deterministic seed selection."""
    num_anchors = max(0, int(config.get("num_anchors", 6)))
    if num_anchors <= 0 or g.num_nodes <= 0:
        return []

    region_size = max(1, int(config.get("anchor_region_size", 128)))

    if num_anchors >= g.num_nodes:
        seeds = list(range(g.num_nodes))
    else:
        perm = g.rng.permutation(np.arange(g.num_nodes))
        seeds = [int(v) for v in perm[:num_anchors]]

    anchors: list[dict] = []
    for anchor_id, seed in enumerate(sorted(seeds)):
        anchors.append(
            {
                "anchor_id": int(anchor_id),
                "seed": int(seed),
                "target_size": int(region_size),
            }
        )

    return anchors


def shell_distribution_from_seed(neigh: dict[int, list[int]], seed: int) -> dict[int, int]:
    """Compute BFS shell distances from seed on adjacency map."""
    seed_i = int(seed)
    if seed_i not in neigh:
        return {}

    dist: dict[int, int] = {seed_i: 0}
    queue: deque[int] = deque([seed_i])

    while queue:
        u = queue.popleft()
        for v in neigh.get(u, []):
            if v in dist:
                continue
            dist[int(v)] = int(dist[u] + 1)
            queue.append(int(v))

    return dist


def rank_quantile_partition_from_dist(
    dist_map: dict[int, int], core_frac: float, mid_frac: float
) -> dict[str, list[int]]:
    """Partition nodes into core/mid/front by rank quantiles of BFS distance."""
    if not dist_map:
        return {"core": [], "mid": [], "front": []}

    core_f = float(np.clip(core_frac, 0.0, 1.0))
    mid_f = float(np.clip(mid_frac, 0.0, 1.0))

    ordered = sorted(dist_map.items(), key=lambda item: (item[1], item[0]))
    n = len(ordered)

    n_core = int(np.floor(core_f * n))
    n_mid = int(np.floor(mid_f * n))
    n_core = max(1, min(n_core, n))
    n_mid = max(0, min(n_mid, n - n_core))

    core_nodes = [int(node) for node, _ in ordered[:n_core]]
    mid_nodes = [int(node) for node, _ in ordered[n_core : n_core + n_mid]]
    front_nodes = [int(node) for node, _ in ordered[n_core + n_mid :]]

    if not front_nodes and mid_nodes:
        front_nodes = [mid_nodes.pop()]

    return {
        "core": core_nodes,
        "mid": mid_nodes,
        "front": front_nodes,
    }


def _shadow_adjacency_for_region(g: GraphState, region_nodes: list[int]) -> dict[int, list[int]]:
    region_set = set(int(n) for n in region_nodes)
    adj: dict[int, list[int]] = {}

    for u in sorted(region_set):
        nbrs = sorted(v for v in active_undirected_neighbors(g, u) if v in region_set)
        adj[int(u)] = [int(v) for v in nbrs]

    return adj


def _subset_adjacency(adj: dict[int, list[int]], nodes: list[int]) -> dict[int, list[int]]:
    node_set = set(int(n) for n in nodes)
    out: dict[int, list[int]] = {}
    for u in sorted(node_set):
        out[int(u)] = [int(v) for v in adj.get(u, []) if v in node_set]
    return out


def _estimate_ds_on_subset(adj: dict[int, list[int]], nodes: list[int], config: dict, rng: np.random.Generator) -> float | None:
    if len(nodes) < 2:
        return None

    taus = [int(t) for t in config.get("k6_taus", [1, 2, 4, 8, 16])]
    walkers = int(config.get("k6_walkers", 256))
    sub_adj = _subset_adjacency(adj, nodes)

    probs = _estimate_return_probabilities(sub_adj, taus, max(1, walkers), rng)
    return _estimate_spectral_dimension(probs)


def _compute_iso_defect(
    adj: dict[int, list[int]], dist_map: dict[int, int], seed: int
) -> tuple[float | None, int | None, int | None, bool]:
    """
    Compute an anchor-local isotropy defect from branch-descendant imbalance.

    Branches are defined by the first hop from the seed along deterministic BFS.
    Returns (iso_defect, branch_count, shell_used, iso_valid).
    """
    seed_i = int(seed)
    if seed_i not in dist_map:
        return None, None, None, False

    first_hop: dict[int, int | None] = {seed_i: None}
    queue: deque[int] = deque([seed_i])

    while queue:
        u = queue.popleft()
        for v in adj.get(u, []):
            if v in first_hop:
                continue
            if u == seed_i:
                first_hop[int(v)] = int(v)
            else:
                first_hop[int(v)] = first_hop.get(u)
            queue.append(int(v))

    branch_counts: dict[int, int] = {}
    for node, hop in first_hop.items():
        if node == seed_i or hop is None:
            continue
        branch_counts[int(hop)] = int(branch_counts.get(int(hop), 0) + 1)

    k = int(len(branch_counts))
    if k < 2:
        return None, k, 1, False

    counts = np.array([float(c) for c in branch_counts.values()], dtype=np.float64)
    total = float(np.sum(counts))
    if total <= 0.0:
        return None, k, 1, False

    probs = counts / total
    uniform = 1.0 / float(k)
    iso_defect = float(0.5 * np.sum(np.abs(probs - uniform)))
    return iso_defect, k, 1, True


def measure_anchor(g: GraphState, anchor: dict, config: dict) -> dict | None:
    """Measure anchor-local fixed-seed geometry. Returns None when invalid."""
    seed = int(anchor.get("seed", -1))
    anchor_id = int(anchor.get("anchor_id", -1))
    target_size = int(anchor.get("target_size", config.get("anchor_region_size", 128)))
    min_region = max(2, int(config.get("anchor_min_region", 24)))

    region_nodes = sample_bfs_region_from_seed(g, seed=seed, target_size=target_size)
    if len(region_nodes) < min_region:
        return None

    shadow_adj = _shadow_adjacency_for_region(g, region_nodes)
    dist_map = shell_distribution_from_seed(shadow_adj, seed)
    if len(dist_map) < min_region:
        return None

    core_frac = float(config.get("k6_core_frac", 0.25))
    mid_frac = float(config.get("k6_mid_frac", 0.50))
    partition = rank_quantile_partition_from_dist(dist_map, core_frac=core_frac, mid_frac=mid_frac)

    core_nodes = partition["core"]
    mid_nodes = partition["mid"]
    front_nodes = partition["front"]

    deg_vals = [len(shadow_adj.get(u, [])) for u in dist_map]
    shadow_mean_degree = float(np.mean(np.array(deg_vals, dtype=np.float64))) if deg_vals else 0.0

    taus = [int(t) for t in config.get("k6_taus", [1, 2, 4, 8, 16])]
    walkers = int(config.get("k6_walkers", 256))
    return_probs = _estimate_return_probabilities(shadow_adj, taus, max(1, walkers), g.rng)

    ds_global = _estimate_spectral_dimension(return_probs)
    dv_global = _estimate_volume_growth_dimension(shadow_adj, root=seed)

    ds_core = _estimate_ds_on_subset(shadow_adj, core_nodes, config, g.rng)
    ds_mid = _estimate_ds_on_subset(shadow_adj, mid_nodes, config, g.rng)
    ds_front = _estimate_ds_on_subset(shadow_adj, front_nodes, config, g.rng)

    reachable = len(dist_map)
    region_fraction = float(reachable / max(1, g.num_nodes))
    mean_shells = float(np.mean(np.array(list(dist_map.values()), dtype=np.float64)))
    iso_defect, iso_branch_count, iso_shell_used, iso_valid = _compute_iso_defect(shadow_adj, dist_map, seed)

    core_ds = float(ds_core) if ds_core is not None else None
    front_ds = float(ds_front) if ds_front is not None else None
    g_fc = None
    if core_ds is not None and front_ds is not None:
        g_fc = float(front_ds - core_ds)

    record = {
        "anchor_id": int(anchor_id),
        "seed": int(seed),
        "region_nodes": int(reachable),
        "region_fraction": float(region_fraction),
        "shadow_mean_degree": float(shadow_mean_degree),
        "ds_global": float(ds_global) if ds_global is not None else None,
        "dv_global": float(dv_global) if dv_global is not None else None,
        "n_core": int(len(core_nodes)),
        "n_mid": int(len(mid_nodes)),
        "n_front": int(len(front_nodes)),
        "ds_core": core_ds,
        "ds_mid": float(ds_mid) if ds_mid is not None else None,
        "ds_front": front_ds,
        "g_fc": g_fc,
        "iso_defect": float(iso_defect) if iso_defect is not None else None,
        "iso_branch_count": int(iso_branch_count) if iso_branch_count is not None else None,
        "iso_shell_used": int(iso_shell_used) if iso_shell_used is not None else None,
        "iso_valid": bool(iso_valid),
        "mean_shells": float(mean_shells),
        "core_max_d": int(max((dist_map[n] for n in core_nodes), default=0)),
        "front_min_d": int(min((dist_map[n] for n in front_nodes), default=0)),
    }
    return record


def measure_k7(step: int, g: GraphState, anchors: list[dict], config: dict) -> list[dict]:
    """Measure all anchors at one step and emit JSON-safe records."""
    records: list[dict] = []

    min_start_nodes = max(1, int(config.get("k6_min_start_nodes", 2)))
    if g.num_nodes < min_start_nodes:
        return records

    for anchor in anchors:
        record = measure_anchor(g, anchor, config)
        if record is None:
            continue
        record["step"] = int(step)
        records.append(record)

    return records
