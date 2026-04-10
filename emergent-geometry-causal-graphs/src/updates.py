from __future__ import annotations

import math
from collections import deque

import numpy as np

from .ancestry import Ancestry, register_node
from .graph_model import (
    GraphState,
    active_undirected_neighbors,
    add_edge,
    add_node,
    current_mean_weight,
    deactivate_edge,
    infer_new_node_level,
    local_shadow_degree,
    recompute_node_state,
    shared_neighbor_fraction_from_sets,
)


def _cfg(config: dict, key: str, default):
    return config.get(key, default)


def density_pressure(k: float, config: dict) -> float:
    k_target = float(_cfg(config, "k_target", 4.0))
    return max(0.0, (k - k_target) / max(k_target, 1e-9))


def effective_wmin(g: GraphState, j: int, config: dict):
    w_min = float(_cfg(config, "w_min", 0.10))
    prune_lambda = float(_cfg(config, "prune_lambda", 0.35))

    p = density_pressure(float(g.active_in_degree[j]), config)
    base = w_min * (1.0 + prune_lambda * p)

    if not bool(_cfg(config, "enable_weight_calibration", True)):
        return base

    target_mean_w = float(_cfg(config, "target_mean_w", 0.60))
    weight_tol = float(_cfg(config, "weight_tol", 0.05))
    prune_lift_alpha = float(_cfg(config, "prune_lift_alpha", 0.70))

    mw = g.global_mean_weight_snapshot
    excess = max(0.0, mw - (target_mean_w + weight_tol))
    lift = 1.0 + prune_lift_alpha * excess
    return base * lift


def local_density_score(g: GraphState, i: int, config: dict) -> float:
    target_density = float(_cfg(config, "target_density", 0.30))
    target = target_density * max(g.num_nodes - 1, 1)
    return 1.0 / (1.0 + abs(float(g.active_out_degree[i]) - target))


def novelty_score(g: GraphState, i: int) -> float:
    return 1.0 / (1.0 + float(g.active_out_degree[i]))


def weighted_choice(g: GraphState, items, scores):
    n = len(items)
    if n == 0:
        return None

    scores = np.asarray(scores, dtype=np.float64)
    scores = np.where(np.isfinite(scores), scores, 0.0)
    scores = np.maximum(scores, 0.0)
    s = scores.sum()

    if s <= 0.0:
        return items[int(g.rng.integers(0, n))]

    probs = scores / s
    idx = int(g.rng.choice(n, p=probs))
    return items[idx]


def ancestry_signature(g: GraphState, node: int, config: dict):
    max_depth = int(_cfg(config, "ancestry_depth", 3))
    cap = int(_cfg(config, "ancestry_cap", 24))

    sig = set()
    frontier = [node]
    seen = {node}

    for _depth in range(1, max_depth + 1):
        nxt = []
        for u in frontier:
            for eid in g.in_edges[u]:
                if not g.active[eid]:
                    continue
                v = g.src[eid]
                if v in seen:
                    continue
                seen.add(v)
                sig.add(v)
                nxt.append(v)
                if len(sig) >= cap:
                    return sig
        frontier = nxt
        if not frontier:
            break
    return sig


def jaccard_sets(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    if union == 0:
        return 0.0
    return inter / union


def local_two_hop_ball(g: GraphState, center: int, radius: int):
    if center >= g.num_nodes:
        return set()

    q = deque([(center, 0)])
    seen = {center}

    while q:
        u, d = q.popleft()
        if d >= radius:
            continue
        for v in active_undirected_neighbors(g, u):
            if v not in seen:
                seen.add(v)
                q.append((v, d + 1))
    return seen


def triangle_support_score_from_sets(ni: set, nj: set):
    if not ni or not nj:
        return 0.0
    inter = len(ni & nj)
    denom = max(1, min(len(ni), len(nj)))
    return inter / denom


def two_hop_coverage_gain(g: GraphState, i: int, j_neighbors: set):
    if not j_neighbors:
        return 0.0

    i_ball = local_two_hop_ball(g, i, radius=2)
    novel = len(i_ball - j_neighbors)
    overlap = len(i_ball & j_neighbors)

    if novel + overlap == 0:
        return 0.0
    return novel / (novel + overlap)


def ball_integrity_term(g: GraphState, i: int, j: int, config: dict):
    if not bool(_cfg(config, "enable_ball_integrity_contrast", True)):
        return 0.0

    if j < int(_cfg(config, "ball_min_node_age", 150)):
        return 0.0

    nj = active_undirected_neighbors(g, j)
    deg_j = len(nj)
    if deg_j < 2:
        return 0.0

    ni = active_undirected_neighbors(g, i)

    tri = triangle_support_score_from_sets(ni, nj)
    twohop = two_hop_coverage_gain(g, i, nj)
    shared = shared_neighbor_fraction_from_sets(ni, nj)
    deg_support = min(1.0, deg_j / max(1.0, float(_cfg(config, "k_target", 4.0))))

    raw = (
        float(_cfg(config, "ball_w_tri", 0.90)) * tri
        + float(_cfg(config, "ball_w_twohop", 0.75)) * twohop
        + float(_cfg(config, "ball_w_deg", 0.20)) * deg_support
        + float(_cfg(config, "ball_w_shared", -0.40)) * shared
    )

    term = float(_cfg(config, "ball_alpha", 0.040)) * raw
    cap = float(_cfg(config, "ball_term_cap", 0.12))
    return max(-cap, min(cap, term))


def weight_centering_drag(g: GraphState, current_w: float, config: dict):
    if not bool(_cfg(config, "enable_weight_calibration", True)):
        return 0.0

    target_mean_w = float(_cfg(config, "target_mean_w", 0.60))
    weight_tol = float(_cfg(config, "weight_tol", 0.05))
    mw = g.global_mean_weight_snapshot
    excess_global = mw - target_mean_w

    if abs(excess_global) <= weight_tol:
        return 0.0

    edge_excess = current_w - target_mean_w
    if excess_global > 0:
        return float(_cfg(config, "weight_center_alpha", 0.060)) * excess_global * max(0.0, edge_excess)
    return 0.0


def excess_weight_penalty(current_w: float, config: dict):
    if not bool(_cfg(config, "enable_weight_calibration", True)):
        return 0.0
    target_mean_w = float(_cfg(config, "target_mean_w", 0.60))
    weight_tol = float(_cfg(config, "weight_tol", 0.05))
    excess = max(0.0, current_w - (target_mean_w + weight_tol))
    return float(_cfg(config, "excess_weight_alpha", 0.045)) * excess


def bfs_ball_profile(g: GraphState, center: int, config: dict):
    r_max = int(_cfg(config, "v9_r_max", 3))
    neigh0 = list(active_undirected_neighbors(g, center))
    if len(neigh0) == 0:
        return {center: 0}, {}, {0: {center}}

    dist = {center: 0}
    first_branch = {}
    shells = {0: {center}}
    q = deque()

    for nb in neigh0:
        dist[nb] = 1
        first_branch[nb] = nb
        shells.setdefault(1, set()).add(nb)
        q.append((nb, 1))

    while q:
        u, d = q.popleft()
        if d >= r_max:
            continue
        for v in active_undirected_neighbors(g, u):
            if v not in dist:
                dist[v] = d + 1
                first_branch[v] = first_branch[u]
                shells.setdefault(d + 1, set()).add(v)
                q.append((v, d + 1))

    for r in range(r_max + 1):
        shells.setdefault(r, set())

    return dist, first_branch, shells


def sector_balance_gain(g: GraphState, i: int, center: int, first_branch: dict, shells: dict):
    center_neighbors = list(active_undirected_neighbors(g, center))
    if len(center_neighbors) < 2:
        return 0.0

    branch_counts = {}
    for r in (2, 3):
        for u in shells.get(r, set()):
            b = first_branch.get(u, None)
            if b is not None:
                branch_counts[b] = branch_counts.get(b, 0) + 1

    if not branch_counts:
        return 0.0

    counts = np.array(list(branch_counts.values()), dtype=np.float64)
    mean_c = float(np.mean(counts))
    if mean_c <= 0:
        return 0.0

    underfilled = {b for b, c in branch_counts.items() if c < mean_c}

    i_ball = local_two_hop_ball(g, i, radius=2)
    touched = 0
    for u in i_ball:
        b = first_branch.get(u, None)
        if b in underfilled:
            touched += 1

    return touched / max(1, len(i_ball))


def front_support_gain(g: GraphState, i: int, shells: dict):
    s2 = shells.get(2, set())
    s3 = shells.get(3, set())
    i_ball = local_two_hop_ball(g, i, radius=2)

    gain_r3 = len(i_ball - s3 - s2)
    overlap_inner = len(i_ball & s2)

    if gain_r3 + overlap_inner == 0:
        return 0.0
    return gain_r3 / (gain_r3 + overlap_inner)


def redundant_inner_overlap(g: GraphState, i: int, shells: dict):
    s1 = shells.get(1, set())
    s2 = shells.get(2, set())
    i_ball = local_two_hop_ball(g, i, radius=2)

    inner_overlap = len(i_ball & (s1 | s2))
    total = len(i_ball)
    if total == 0:
        return 0.0
    return inner_overlap / total


def v9_ball_coherence_term(g: GraphState, i: int, j: int, config: dict):
    if not bool(_cfg(config, "enable_v9_ball_coherence", False)):
        return 0.0
    if j < int(_cfg(config, "v9_min_node_age", 300)):
        return 0.0

    _, first_branch, shells = bfs_ball_profile(g, j, config)
    if len(shells.get(2, set())) < 3:
        return 0.0

    novel_r2 = two_hop_coverage_gain(g, i, shells.get(1, set()) | shells.get(2, set()))
    novel_r3 = front_support_gain(g, i, shells)
    sec_gain = sector_balance_gain(g, i, j, first_branch, shells)
    red_inner = redundant_inner_overlap(g, i, shells)

    raw = (
        float(_cfg(config, "v9_w_r2", 0.55)) * novel_r2
        + float(_cfg(config, "v9_w_r3", 0.85)) * novel_r3
        + float(_cfg(config, "v9_w_sector", 0.90)) * sec_gain
        - float(_cfg(config, "v9_w_redundant", 0.60)) * red_inner
    )

    s2 = len(shells.get(2, set()))
    s3 = len(shells.get(3, set()))
    thin_front = max(0.0, (s2 - s3) / s2) if s2 > 0 else 0.0
    raw += float(_cfg(config, "v9_w_front", 0.70)) * thin_front * novel_r3

    term = float(_cfg(config, "v9_alpha", 0.035)) * raw
    cap = float(_cfg(config, "v9_term_cap", 0.10))
    return max(-cap, min(cap, term))


def choose_parents_for_new_node(g: GraphState, config: dict):
    if g.num_nodes <= 0:
        return []

    m = int(_cfg(config, "m_parents", 4))
    pool_size = min(int(_cfg(config, "candidate_pool", 64)), g.num_nodes)
    candidate_ids = g.rng.choice(g.num_nodes, size=pool_size, replace=False).tolist()

    alpha = float(_cfg(config, "alpha", 1.10))
    beta = float(_cfg(config, "beta", 0.70))
    gamma = float(_cfg(config, "gamma", 0.35))

    base_scores = {}
    sig_cache = {}
    for i in candidate_ids:
        ld = local_density_score(g, i, config)
        coh = float(g.node_coherence_ema[i])
        nov = novelty_score(g, i)
        base_scores[i] = math.exp(alpha * ld + beta * coh + gamma * nov)

    repulsion_lambda = float(_cfg(config, "repulsion_lambda", 0.50))

    chosen = []
    chosen_sigs = []
    while len(chosen) < min(m, len(candidate_ids)):
        remaining = [i for i in candidate_ids if i not in chosen]
        if not remaining:
            break

        scores = []
        for i in remaining:
            if i not in sig_cache:
                sig_cache[i] = ancestry_signature(g, i, config)

            repulsion_factor = 1.0
            for sig_p in chosen_sigs:
                sim = jaccard_sets(sig_cache[i], sig_p)
                repulsion_factor *= max(0.05, 1.0 - repulsion_lambda * sim)

            scores.append(base_scores[i] * repulsion_factor)

        pick = weighted_choice(g, remaining, scores)
        if pick is None:
            break
        chosen.append(pick)
        chosen_sigs.append(sig_cache[pick])

    return chosen


def relax_random_nodes(g: GraphState, config: dict):
    if g.num_nodes <= 1:
        return

    batch_size = min(int(_cfg(config, "node_relax_batch", 32)), g.num_nodes - 1)
    nodes = g.rng.choice(np.arange(1, g.num_nodes), size=batch_size, replace=False)
    for j in nodes:
        g.state[j] = recompute_node_state(g, int(j))


def update_edge(g: GraphState, eid: int, config: dict):
    if not g.active[eid]:
        return

    i = g.src[eid]
    j = g.dst[eid]
    old_w = g.w[eid]

    incoming = [pe for pe in g.in_edges[j] if g.active[pe]]
    m = len(incoming)
    coherence = 1.0 if g.state[i] == g.state[j] else 0.0

    if m <= 1:
        redundancy = mean_sim = conc_pressure = 0.0
        crowd_term = cluster_strength = sim_to_dom = 0.0
        drift_factor = membership = 0.0
    else:
        parent_nodes = [g.src[pe] for pe in incoming]
        sigs = [ancestry_signature(g, u, config) for u in parent_nodes]

        idx_e = incoming.index(eid)
        s_i = g.state[i]
        same = 0
        total_other = 0
        for idx, pe in enumerate(incoming):
            if idx == idx_e:
                continue
            total_other += 1
            if g.state[g.src[pe]] == s_i:
                same += 1
        redundancy = same / total_other if total_other > 0 else 0.0

        sim_mat = np.zeros((m, m), dtype=np.float64)
        q = np.ones(m, dtype=np.float64)
        crowd_load_arr = np.zeros(m, dtype=np.float64)
        cluster_load_arr = np.zeros(m, dtype=np.float64)

        sim_threshold = float(_cfg(config, "sim_threshold", 0.40))
        cross_sim_threshold = float(_cfg(config, "cross_sim_threshold", 0.35))

        for a in range(m):
            for b in range(a + 1, m):
                sim = jaccard_sets(sigs[a], sigs[b])
                sim_mat[a, b] = sim
                sim_mat[b, a] = sim
                q[a] += sim
                q[b] += sim

                if sim >= sim_threshold:
                    excess = (sim - sim_threshold) / (1.0 - sim_threshold + 1e-12)
                    crowd_load_arr[a] += excess * g.w[incoming[b]]
                    crowd_load_arr[b] += excess * g.w[incoming[a]]

                if sim >= cross_sim_threshold:
                    excess2 = (sim - cross_sim_threshold) / (1.0 - cross_sim_threshold + 1e-12)
                    cluster_load_arr[a] += excess2 * g.w[incoming[b]]
                    cluster_load_arr[b] += excess2 * g.w[incoming[a]]

        mean_sim = float(np.sum(sim_mat[idx_e]) / max(1, m - 1))

        qsum = q.sum()
        if qsum <= 0:
            conc_pressure = 0.0
        else:
            p = q / qsum
            concentration = float(np.sum(p * p))
            baseline = 1.0 / m
            conc_pressure = max(0.0, (concentration - baseline) / max(1e-12, 1.0 - baseline))

        crowd_total = float(np.sum(crowd_load_arr))
        if crowd_total <= 1e-12:
            crowd_term = drift_factor = membership = 0.0
        else:
            p_crowd = crowd_load_arr / crowd_total
            c_j = float(np.sum(p_crowd * p_crowd))
            adaptive_factor = 1.0 + float(_cfg(config, "adaptive_alpha", 3.0)) * max(0.0, c_j - float(_cfg(config, "c_target", 0.36)))
            crowd_term = float(_cfg(config, "lambda_crowd", 0.060)) * adaptive_factor * float(crowd_load_arr[idx_e])

            drift_threshold = float(_cfg(config, "drift_threshold", 0.40))
            drift_factor = max(0.0, c_j - drift_threshold) / max(1e-12, 1.0 - drift_threshold)
            dom_idx_drift = int(np.argmax(p_crowd))
            membership = float(sim_mat[idx_e, dom_idx_drift])

        cluster_total = float(np.sum(cluster_load_arr))
        if cluster_total <= 1e-12:
            cluster_strength = sim_to_dom = 0.0
        else:
            p_cluster = cluster_load_arr / cluster_total
            dom_idx = int(np.argmax(p_cluster))
            cluster_strength = float(np.max(p_cluster))
            sim_to_dom = float(sim_mat[idx_e, dom_idx])

    density_p = density_pressure(float(g.active_in_degree[j]), config)
    inhib = float(_cfg(config, "inhib_gamma", 0.080)) * mean_sim * (1.0 + float(_cfg(config, "conc_gamma", 1.20)) * conc_pressure) * (1.0 + density_p)

    sum_in = sum(g.w[pe] for pe in g.in_edges[j] if g.active[pe])
    sum_out = sum(g.w[pe] for pe in g.out_edges[i] if g.active[pe])

    load_eps = float(_cfg(config, "load_eps", 1e-9))
    share_in = old_w / (sum_in + load_eps)
    share_out = old_w / (sum_out + load_eps)
    load_proxy = 0.5 * share_in + 0.5 * share_out

    reward_term = float(_cfg(config, "eta", 0.075)) * (2.0 * coherence - 1.0) / (1.0 + float(_cfg(config, "load_beta", 4.0)) * load_proxy)
    load_drag = float(_cfg(config, "load_gamma", 0.060)) * (load_proxy ** 2)

    ni = active_undirected_neighbors(g, i)
    nj = active_undirected_neighbors(g, j)
    shared_frac = shared_neighbor_fraction_from_sets(ni, nj)

    loop_gate = max(0.0, 1.0 - shared_frac / max(float(_cfg(config, "max_shared_neighbor_frac", 0.22)), 1e-12))
    loop_gate = min(1.0, loop_gate)

    deg_i = len(ni)
    deg_j = len(nj)
    if deg_i <= 0:
        sparse_gate = 1.0
    else:
        ratio = (deg_i - deg_j) / max(1.0, deg_i)
        sparse_gate = 1.0 / (1.0 + math.exp(-float(_cfg(config, "outflow_beta", 1.4)) * ratio))
        sparse_gate = max(0.0, min(1.0, sparse_gate))

    gate = loop_gate * sparse_gate

    active_cluster = max(0.0, cluster_strength - float(_cfg(config, "cross_min_cluster_weight", 0.15)))
    genealogical_novelty = (1.0 - sim_to_dom) ** float(_cfg(config, "genealogical_novelty_beta", 0.8))
    cross_bonus = float(_cfg(config, "cross_alpha", 0.035)) * active_cluster * genealogical_novelty * (1.0 - min(1.0, load_proxy)) * gate

    age = g.current_step - g.edge_birth[eid]
    if bool(_cfg(config, "plasticity_only_on_old", True)) and age < int(_cfg(config, "old_edge_age", 1500)):
        plastic_term = 0.0
    else:
        age_fac = 1.0 - math.exp(-age / float(_cfg(config, "age_tau", 2500.0)))
        plastic_term = min(float(_cfg(config, "plasticity_cap", 0.25)), float(_cfg(config, "age_alpha", 0.090)) * age_fac * drift_factor * membership)

    ball_term = ball_integrity_term(g, i, j, config)
    v9_term = v9_ball_coherence_term(g, i, j, config)

    center_drag = weight_centering_drag(g, old_w, config)
    excess_pen = excess_weight_penalty(old_w, config)

    new_w = (
        old_w
        + reward_term
        + cross_bonus
        + ball_term
        + v9_term
        - float(_cfg(config, "nu", 0.060)) * redundancy
        - inhib
        - crowd_term
        - load_drag
        - plastic_term
        - center_drag
        - excess_pen
        - float(_cfg(config, "mu", 0.020)) * (old_w - float(_cfg(config, "w0", 1.0)))
    )

    if new_w < effective_wmin(g, j, config):
        deactivate_edge(g, eid)
        return

    w_min = float(_cfg(config, "w_min", 0.10))
    w_max = float(_cfg(config, "w_max", 3.0))
    final_w = float(min(w_max, max(new_w, w_min)))
    g.w[eid] = final_w
    g.active_weight_sum += (final_w - old_w)
    g.node_coherence_ema[i] = 0.98 * g.node_coherence_ema[i] + 0.02 * coherence


def update_random_edges(g: GraphState, config: dict):
    n = len(g.active_edge_ids)
    if n == 0:
        return
    batch_size = min(int(_cfg(config, "edge_update_batch", 80)), n)
    idxs = g.rng.choice(n, size=batch_size, replace=False)
    picked_eids = [g.active_edge_ids[int(k)] for k in idxs]
    for eid in picked_eids:
        if g.active[eid]:
            update_edge(g, eid, config)


def initialize_graph(g: GraphState, ancestry: Ancestry, config: dict) -> None:
    init_nodes = int(_cfg(config, "init_nodes", 16))
    m_parents = int(_cfg(config, "m_parents", 4))
    w0 = float(_cfg(config, "w0", 1.0))

    for _ in range(init_nodes):
        s = int(g.rng.integers(0, 2))
        node = add_node(g, s=s, level=0)
        register_node(ancestry, node_id=node, step=0, parents=[])

    for j in range(1, init_nodes):
        prev = list(range(j))
        m0 = min(m_parents, len(prev))
        parents = g.rng.choice(prev, size=m0, replace=False).tolist() if m0 > 0 else []

        lvl = 1 + max(g.node_level[int(p)] for p in parents) if parents else 0
        g.node_level[j] = lvl
        g.current_max_level = max(g.current_max_level, int(lvl))

        register_node(ancestry, node_id=j, step=0, parents=[int(x) for x in parents])
        for p in parents:
            eid = add_edge(g, i=int(p), j=j, weight=w0, current_step=0)
            update_edge(g, eid, config)

    g.global_mean_weight_snapshot = current_mean_weight(g, default_w0=w0)


def step(g: GraphState, ancestry: Ancestry, config: dict) -> None:
    g.current_step += 1
    g.global_mean_weight_snapshot = current_mean_weight(g, default_w0=float(_cfg(config, "w0", 1.0)))

    if g.num_nodes >= int(_cfg(config, "max_nodes", g.num_nodes + 1)):
        relax_random_nodes(g, config)
        update_random_edges(g, config)
        return

    parents = choose_parents_for_new_node(g, config)
    if parents:
        avg = np.mean([g.state[p] for p in parents])
        s_new = 1 if avg >= 0.5 else 0
    else:
        s_new = int(g.rng.integers(0, 2))

    level = infer_new_node_level(g, parents)
    new_node = add_node(g, s=int(s_new), level=level)
    register_node(ancestry, node_id=new_node, step=g.current_step, parents=[int(p) for p in parents])

    w0 = float(_cfg(config, "w0", 1.0))
    new_eids = [add_edge(g, i=int(p), j=new_node, weight=w0, current_step=g.current_step) for p in parents]

    for eid in new_eids:
        update_edge(g, eid, config)

    g.state[new_node] = recompute_node_state(g, new_node)
    relax_random_nodes(g, config)
    update_random_edges(g, config)

    g.global_mean_weight_snapshot = current_mean_weight(g, default_w0=w0)
