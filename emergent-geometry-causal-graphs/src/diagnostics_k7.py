from __future__ import annotations

import bisect
import math
from collections import Counter, deque

import numpy as np

from .diagnostics_k2 import _estimate_return_probabilities, _estimate_spectral_dimension, _estimate_volume_growth_dimension
from .graph_model import GraphState


def sample_bfs_region_from_seed(g: GraphState, seed: int, target_size: int):
    if seed >= g.num_nodes:
        return []

    q = deque([seed])
    seen = {seed}
    region = [seed]

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


def initialize_anchors(g: GraphState, config: dict) -> list[dict]:
    num_anchors = int(config.get("num_anchors", 8))
    candidates = list(range(g.num_nodes))
    g.rng.shuffle(candidates)

    seeds = []
    for u in candidates:
        if len(seeds) >= num_anchors:
            break
        ok = True
        for s in seeds:
            if abs(u - s) < 2:
                ok = False
                break
        if ok:
            seeds.append(u)

    return [{"anchor_id": aid, "seed": int(seed)} for aid, seed in enumerate(seeds)]


def _build_shadow_adjacency(g: GraphState, region_nodes):
    region_set = set(region_nodes)
    neigh = {u: set() for u in region_nodes}
    for eid in g.active_edge_ids:
        i = g.src[eid]
        j = g.dst[eid]
        if i in region_set and j in region_set:
            neigh[i].add(j)
            neigh[j].add(i)
    return neigh


def shell_distribution_from_seed(neigh, seed):
    q = deque([(seed, 0)])
    dist = {seed: 0}

    while q:
        u, d = q.popleft()
        for v in neigh[u]:
            if v not in dist:
                dist[v] = d + 1
                q.append((v, d + 1))

    cnt = Counter(dist.values())
    max_r = max(cnt.keys()) if cnt else 0
    shells = [cnt.get(r, 0) for r in range(max_r + 1)]
    return shells, dist


def rank_quantile_partition_from_dist(dist_map, core_frac=0.50, mid_frac=0.30):
    if not dist_map:
        return [], [], [], None, None

    pairs = sorted(dist_map.items(), key=lambda x: (x[1], x[0]))
    n = len(pairs)

    i_core = int(round(core_frac * n))
    i_mid = int(round((core_frac + mid_frac) * n))

    i_core = max(1, min(i_core, n))
    i_mid = max(i_core, min(i_mid, n))

    core_pairs = pairs[:i_core]
    mid_pairs = pairs[i_core:i_mid]
    front_pairs = pairs[i_mid:]

    core = [u for u, _ in core_pairs]
    mid = [u for u, _ in mid_pairs]
    front = [u for u, _ in front_pairs]

    core_max_d = core_pairs[-1][1] if core_pairs else None
    front_min_d = front_pairs[0][1] if front_pairs else None
    return core, mid, front, core_max_d, front_min_d


def _start_class_ds(full_neigh, start_nodes, taus, n_walkers, rng, min_start_nodes=120):
    valid_starts = [u for u in start_nodes if u in full_neigh and len(full_neigh[u]) > 0]
    if len(valid_starts) < min_start_nodes:
        return None
    probs = _estimate_return_probabilities(full_neigh, taus, n_walkers, rng, start_nodes=valid_starts)
    return _estimate_spectral_dimension(probs)


def bfs_branch_partition(neigh, center):
    first_branch = {}
    dist = {center: 0}
    q = deque([center])

    for nb in neigh[center]:
        first_branch[nb] = nb
        dist[nb] = 1
        q.append(nb)

    while q:
        u = q.popleft()
        for v in neigh[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                first_branch[v] = first_branch[u]
                q.append(v)

    return dist, first_branch


def estimate_isotropy_defect(neigh, region_nodes, rng, radii=(2, 4, 6), num_centers=10):
    candidates = [u for u in region_nodes if len(neigh[u]) >= 3]
    if len(candidates) == 0:
        return None, []

    centers = rng.choice(candidates, size=min(num_centers, len(candidates)), replace=False)
    defects = []

    for center in centers:
        dist, first_branch = bfs_branch_partition(neigh, int(center))
        branch_to_dists = {}

        for u, b in first_branch.items():
            branch_to_dists.setdefault(b, []).append(dist[u])

        for b in branch_to_dists:
            branch_to_dists[b].sort()

        local_defects = []
        for r in radii:
            counts = []
            for _, dlist in branch_to_dists.items():
                counts.append(bisect.bisect_right(dlist, r))
            if len(counts) >= 3 and np.mean(counts) > 0:
                local_defects.append(float(np.std(counts) / np.mean(counts)))

        if local_defects:
            defects.append(float(np.mean(local_defects)))

    if not defects:
        return None, []
    return float(np.mean(defects)), defects


def _estimate_causal_front_proxy(g: GraphState, region_nodes, num_seeds=10, max_depth=8):
    seeds = g.rng.choice(region_nodes, size=min(num_seeds, len(region_nodes)), replace=False)

    shell_profiles = []
    jump_defects = []
    max_depths = []

    for seed in seeds:
        q = deque([(int(seed), 0)])
        dist = {int(seed): 0}

        while q:
            u, d = q.popleft()
            if d >= max_depth:
                continue
            for eid in g.out_edges[u]:
                if not g.active[eid]:
                    continue
                v = g.dst[eid]
                if v not in dist:
                    dist[v] = d + 1
                    q.append((v, d + 1))

        cnt = Counter(dist.values())
        shells = [cnt.get(d, 0) for d in range(1, max_depth + 1)]

        total = max(1, len(dist) - 1)
        cum_frac = np.cumsum(shells) / total
        jump_defect = float(cum_frac[min(1, len(cum_frac) - 1)]) if len(cum_frac) > 0 else 0.0
        max_depth_found = max(dist.values()) if len(dist) > 0 else 0

        shell_profiles.append(shells)
        jump_defects.append(jump_defect)
        max_depths.append(max_depth_found)

    mean_shells = list(np.mean(np.array(shell_profiles, dtype=np.float64), axis=0))
    return {
        "jump_defect": float(np.mean(jump_defects)),
        "mean_shell_sizes": mean_shells,
        "max_depth_found_mean": float(np.mean(max_depths)),
    }


def measure_anchor(g: GraphState, anchor: dict, config: dict) -> dict | None:
    seed = int(anchor["seed"])
    if seed >= g.num_nodes:
        return None

    region_live = sample_bfs_region_from_seed(g, seed, int(config.get("anchor_region_size", 1500)))
    if len(region_live) < int(config.get("anchor_min_region", 100)):
        return None

    full_neigh = _build_shadow_adjacency(g, region_live)
    if seed not in full_neigh or len(full_neigh[seed]) == 0:
        connected = [u for u in region_live if u in full_neigh and len(full_neigh[u]) > 0]
        if not connected:
            return None
        seed = connected[0]

    taus = [int(t) for t in config.get("k2_taus", [2, 4, 8, 16])]
    walkers = int(config.get("k2_walkers", 800))
    ret_probs = _estimate_return_probabilities(full_neigh, taus, walkers, g.rng)
    ds_global = _estimate_spectral_dimension(ret_probs)
    dv_global = _estimate_volume_growth_dimension(full_neigh, region_live, g.rng)
    shadow_deg = float(np.mean([len(full_neigh[u]) for u in region_live]))

    iso_defect, _ = estimate_isotropy_defect(
        full_neigh,
        region_live,
        g.rng,
        radii=tuple(config.get("k3_radii", [2, 4, 6])),
        num_centers=int(config.get("k3_num_centers", 10)),
    )

    causal = _estimate_causal_front_proxy(
        g,
        region_live,
        num_seeds=int(config.get("k3_num_seeds", 10)),
        max_depth=int(config.get("k3_max_depth", 8)),
    )

    _, dist = shell_distribution_from_seed(full_neigh, seed)
    core, mid, front, core_max_d, front_min_d = rank_quantile_partition_from_dist(
        dist,
        core_frac=float(config.get("k6_core_frac", 0.50)),
        mid_frac=float(config.get("k6_mid_frac", 0.30)),
    )

    k6_taus = [int(t) for t in config.get("k6_taus", [2, 4, 8, 16])]
    k6_walkers = int(config.get("k6_walkers", 800))
    min_start_nodes = int(config.get("k6_min_start_nodes", 120))

    ds_core = _start_class_ds(full_neigh, core, k6_taus, k6_walkers, g.rng, min_start_nodes)
    ds_mid = _start_class_ds(full_neigh, mid, k6_taus, k6_walkers, g.rng, min_start_nodes)
    ds_front = _start_class_ds(full_neigh, front, k6_taus, k6_walkers, g.rng, min_start_nodes)

    g_fm = None if (ds_front is None or ds_mid is None) else (ds_front - ds_mid)
    g_mc = None if (ds_mid is None or ds_core is None) else (ds_mid - ds_core)
    g_fc = None if (ds_front is None or ds_core is None) else (ds_front - ds_core)

    # auxiliary surrogate for audit/debug only
    iso_surrogate = None
    if len(full_neigh[seed]) >= 2:
        counts = [len(full_neigh[n]) for n in full_neigh[seed]]
        m = np.mean(counts)
        if m > 0:
            iso_surrogate = float(np.std(counts) / m)

    return {
        "anchor_id": anchor["anchor_id"],
        "seed": anchor["seed"],
        "seed_used": seed,
        "region_nodes": len(region_live),
        "region_fraction": len(region_live) / max(1, g.num_nodes),
        "shadow_mean_degree": shadow_deg,
        "return_probs": ret_probs,
        "ds_global": ds_global,
        "dv_global": dv_global,
        "iso_defect": iso_defect,
        "iso_defect_surrogate": iso_surrogate,
        "jump_defect": causal["jump_defect"],
        "mean_max_depth": causal["max_depth_found_mean"],
        "mean_shells": causal["mean_shell_sizes"],
        "n_core": len(core),
        "n_mid": len(mid),
        "n_front": len(front),
        "core_max_d": core_max_d,
        "front_min_d": front_min_d,
        "ds_core": ds_core,
        "ds_mid": ds_mid,
        "ds_front": ds_front,
        "g_fm": g_fm,
        "g_mc": g_mc,
        "g_fc": g_fc,
    }


def measure_k7(step: int, g: GraphState, anchors: list[dict], config: dict) -> list[dict]:
    out = []
    for anchor in anchors:
        record = measure_anchor(g, anchor, config)
        if record is not None:
            record["step"] = int(step)
            out.append(record)
    return out
