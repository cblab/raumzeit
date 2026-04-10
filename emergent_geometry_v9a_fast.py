# V9-A-fast = V8a-fast + coarse-grained ball coherence term
# ------------------------------------------------------------
# Idee:
#   V8a-fast war noch lokal-kantenbezogen.
#   V9-A ergänzt einen mesoskopischen Term:
#
#   Eine Kante ist gut, wenn sie den BFS-Ball um den Zielknoten
#   über mehrere Skalen (r = 1,2,3) kohärenter macht.
#
#   Gemessen wird nicht "perfekte Geometrie", sondern:
#   - unterstützt die Kante die äußeren Schalen?
#   - reduziert sie Sektor-Ungleichgewicht über mehrere Radien?
#   - verhindert sie, dass der Ball innen dicht, außen aber dünn bleibt?
#
# FAST-Variante:
#   - nur surrogates, keine hypothetische Full-Rebuild-Simulation
#   - lokales r<=3 BFS
#   - sector-balance grob über first-branch assignment
# ------------------------------------------------------------

import math
import random
import bisect
from collections import deque, Counter

import numpy as np


# ============================================================
# SETTINGS
# ============================================================

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
rng = np.random.default_rng(SEED)

# Runtime
N_TOTAL = 20000
N0 = 16
MAX_NODES = N0 + N_TOTAL + 100
M_PARENTS = 4
MEASURE_EVERY = 500

# Parent selection
CANDIDATE_POOL = 64
TARGET_DENSITY = 0.30
ALPHA = 1.10
BETA = 0.70
GAMMA = 0.35

# Genealogical repulsion at birth
REPULSION_LAMBDA = 0.50
ANCESTRY_DEPTH = 3
ANCESTRY_CAP = 24

# Edge / state dynamics
W0 = 1.0
W_MIN = 0.10
W_MAX = 3.0

ETA = 0.075
NU = 0.060
MU = 0.020

# Mesoscopic suppression
INHIB_GAMMA = 0.080
CONC_GAMMA = 1.20

# Sparse baseline
PRUNE_LAMBDA = 0.35
K_TARGET = 4.0

# Adaptive crowding
LAMBDA_CROWD = 0.060
SIM_THRESHOLD = 0.40
C_TARGET = 0.36
ADAPTIVE_ALPHA = 3.0

# V4.0 global load saturation
LOAD_BETA = 4.0
LOAD_GAMMA = 0.060
LOAD_EPS = 1e-9

# V4.3 topological outflow bonus
CROSS_ALPHA = 0.035
CROSS_SIM_THRESHOLD = 0.35
CROSS_MIN_CLUSTER_WEIGHT = 0.15
MAX_SHARED_NEIGHBOR_FRAC = 0.22
OUTFLOW_BETA = 1.4
GENEALOGICAL_NOVELTY_BETA = 0.8

# V5.0 plasticity
AGE_ALPHA = 0.090
AGE_TAU = 2500.0
DRIFT_THRESHOLD = 0.40
PLASTICITY_CAP = 0.25
PLASTICITY_ONLY_ON_OLD = True
OLD_EDGE_AGE = 1500

# Update schedule
EDGE_UPDATE_BATCH = 80
NODE_RELAX_BATCH = 32

# Global K2 cadence
K2_GLOBAL_EVERY = 2000
K2_REGION_SIZE = 1500
K2_TAUS = [2, 4, 8, 16]
K2_WALKERS = 800

# K3 / K7 isotropy radii
K3_RADII = [2, 4, 6]
K3_NUM_CENTERS = 10
K3_NUM_SEEDS = 10
K3_MAX_DEPTH = 8

# K4 / K5 cadence
K4_MEASURE_EVERY = 2000
K5_MEASURE_EVERY = 4000
K4_PAIR_SAMPLES = 300

# K6.3
K6_TAUS = [2, 4, 8, 16]
K6_WALKERS = 800
K6_MIN_START_NODES = 120

# rank quantiles for K6.3
K6_CORE_FRAC = 0.50
K6_MID_FRAC = 0.30
K6_FRONT_FRAC = 0.20

# K7 anchors
NUM_ANCHORS = 8
ANCHOR_REGION_SIZE = 1500
ANCHOR_MIN_REGION = 100

# Standard K7 cadence
K7_EVERY = 500

# Fine window
FINE_START = 10000
FINE_END = 16000
FINE_EVERY = 250

ENABLE_EARLY_STOP = False

# ------------------------------------------------------------
# V8a-fast contrast mechanism:
# Ball-integrity reward
# ------------------------------------------------------------
ENABLE_BALL_INTEGRITY_CONTRAST = True
BALL_MIN_NODE_AGE = 150
BALL_RADIUS = 2
BALL_ALPHA = 0.040
BALL_TERM_CAP = 0.12

BALL_W_TRI = 0.90
BALL_W_TWOHOP = 0.75
BALL_W_BRIDGE = 0.00
BALL_W_DEG = 0.20
BALL_W_SHARED = -0.40

# ------------------------------------------------------------
# V8a-fast calibration:
# keep weight regime closer to baseline
# ------------------------------------------------------------
ENABLE_WEIGHT_CALIBRATION = True
TARGET_MEAN_W = 0.60
WEIGHT_CENTER_ALPHA = 0.060
EXCESS_WEIGHT_ALPHA = 0.045
PRUNE_LIFT_ALPHA = 0.70
WEIGHT_TOL = 0.05

# ------------------------------------------------------------
# V9-A new term:
# coarse-grained ball coherence
# ------------------------------------------------------------
ENABLE_V9_BALL_COHERENCE = True
V9_MIN_NODE_AGE = 300
V9_ALPHA = 0.035
V9_TERM_CAP = 0.10
V9_R_MAX = 3

V9_W_R2 = 0.55
V9_W_R3 = 0.85
V9_W_SECTOR = 0.90
V9_W_FRONT = 0.70
V9_W_REDUNDANT = 0.60


# ============================================================
# GRAPH STORAGE
# ============================================================

src = []
dst = []
w = []
active = []
active_pos = []
edge_birth = []

active_edge_ids = []

out_edges = [[] for _ in range(MAX_NODES)]
in_edges = [[] for _ in range(MAX_NODES)]

state = np.zeros(MAX_NODES, dtype=np.int8)
node_coherence_ema = np.full(MAX_NODES, 0.5, dtype=np.float64)

active_in_degree = np.zeros(MAX_NODES, dtype=np.int32)
active_out_degree = np.zeros(MAX_NODES, dtype=np.int32)

node_level = np.zeros(MAX_NODES, dtype=np.int32)
current_max_level = 0
num_nodes = 0
current_step = 0

# fast global weight accounting
active_weight_sum = 0.0
active_edge_count = 0
global_mean_weight_snapshot = W0


# ============================================================
# BASIC HELPERS
# ============================================================

def add_node(s: int, level: int = 0) -> int:
    global num_nodes, current_max_level
    idx = num_nodes
    state[idx] = s
    node_coherence_ema[idx] = 0.5
    active_in_degree[idx] = 0
    active_out_degree[idx] = 0
    node_level[idx] = int(level)

    if level > current_max_level:
        current_max_level = int(level)

    num_nodes += 1
    return idx


def add_edge(i: int, j: int, weight: float = W0) -> int:
    global active_weight_sum, active_edge_count

    eid = len(src)
    src.append(i)
    dst.append(j)
    w.append(float(weight))
    active.append(True)
    active_pos.append(len(active_edge_ids))
    active_edge_ids.append(eid)
    edge_birth.append(current_step)

    out_edges[i].append(eid)
    in_edges[j].append(eid)

    active_out_degree[i] += 1
    active_in_degree[j] += 1

    active_weight_sum += float(weight)
    active_edge_count += 1
    return eid


def deactivate_edge(eid: int):
    global active_weight_sum, active_edge_count

    if not active[eid]:
        return

    active_weight_sum -= w[eid]
    active_edge_count -= 1

    active[eid] = False
    i = src[eid]
    j = dst[eid]

    active_out_degree[i] -= 1
    active_in_degree[j] -= 1

    pos = active_pos[eid]
    last = active_edge_ids[-1]
    active_edge_ids[pos] = last
    active_pos[last] = pos
    active_edge_ids.pop()


def density_pressure(k: float) -> float:
    return max(0.0, (k - K_TARGET) / max(K_TARGET, 1e-9))


def current_mean_weight():
    if active_edge_count <= 0:
        return W0
    return active_weight_sum / active_edge_count


def effective_wmin(j: int):
    p = density_pressure(float(active_in_degree[j]))
    base = W_MIN * (1.0 + PRUNE_LAMBDA * p)

    if not ENABLE_WEIGHT_CALIBRATION:
        return base

    mw = global_mean_weight_snapshot
    excess = max(0.0, mw - (TARGET_MEAN_W + WEIGHT_TOL))
    lift = 1.0 + PRUNE_LIFT_ALPHA * excess
    return base * lift


def local_density_score(i: int) -> float:
    target = TARGET_DENSITY * max(num_nodes - 1, 1)
    return 1.0 / (1.0 + abs(float(active_out_degree[i]) - target))


def novelty_score(i: int) -> float:
    return 1.0 / (1.0 + float(active_out_degree[i]))


def weighted_choice(items, scores):
    n = len(items)
    if n == 0:
        return None

    scores = np.asarray(scores, dtype=np.float64)
    scores = np.where(np.isfinite(scores), scores, 0.0)
    scores = np.maximum(scores, 0.0)
    s = scores.sum()

    if s <= 0.0:
        return items[int(rng.integers(0, n))]

    probs = scores / s
    idx = int(rng.choice(n, p=probs))
    return items[idx]


def active_weights_np():
    if not active_edge_ids:
        return np.array([], dtype=np.float64)
    return np.fromiter((w[eid] for eid in active_edge_ids), dtype=np.float64)


# ============================================================
# ANCESTRY SIGNATURES
# ============================================================

def ancestry_signature(node: int, max_depth: int = ANCESTRY_DEPTH, cap: int = ANCESTRY_CAP):
    sig = set()
    frontier = [node]
    seen = {node}

    for _depth in range(1, max_depth + 1):
        nxt = []
        for u in frontier:
            for eid in in_edges[u]:
                if not active[eid]:
                    continue
                v = src[eid]
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


# ============================================================
# LOCAL TOPOLOGY HELPERS
# ============================================================

def active_undirected_neighbors(u: int):
    nbrs = set()
    for eid in out_edges[u]:
        if active[eid]:
            nbrs.add(dst[eid])
    for eid in in_edges[u]:
        if active[eid]:
            nbrs.add(src[eid])
    return nbrs


def shared_neighbor_fraction_from_sets(ni: set, nj: set):
    if not ni and not nj:
        return 0.0
    inter = len(ni & nj)
    union = len(ni | nj)
    if union == 0:
        return 0.0
    return inter / union


def local_shadow_degree(u: int):
    return len(active_undirected_neighbors(u))


# ============================================================
# V8a-fast BALL-INTEGRITY HELPERS
# ============================================================

def local_two_hop_ball(center: int, radius: int = BALL_RADIUS):
    if center >= num_nodes:
        return set()

    q = deque([(center, 0)])
    seen = {center}

    while q:
        u, d = q.popleft()
        if d >= radius:
            continue
        for v in active_undirected_neighbors(u):
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


def two_hop_coverage_gain(i: int, j_neighbors: set):
    if not j_neighbors:
        return 0.0

    i_ball = local_two_hop_ball(i, radius=2)
    novel = len(i_ball - j_neighbors)
    overlap = len(i_ball & j_neighbors)

    if novel + overlap == 0:
        return 0.0
    return novel / (novel + overlap)


def ball_integrity_term(i: int, j):
    if not ENABLE_BALL_INTEGRITY_CONTRAST:
        return 0.0

    if j < BALL_MIN_NODE_AGE:
        return 0.0

    nj = active_undirected_neighbors(j)
    deg_j = len(nj)
    if deg_j < 2:
        return 0.0

    ni = active_undirected_neighbors(i)

    tri = triangle_support_score_from_sets(ni, nj)
    twohop = two_hop_coverage_gain(i, nj)
    shared = shared_neighbor_fraction_from_sets(ni, nj)
    deg_support = min(1.0, deg_j / max(1.0, K_TARGET))

    raw = (
        BALL_W_TRI * tri
        + BALL_W_TWOHOP * twohop
        + BALL_W_DEG * deg_support
        + BALL_W_SHARED * shared
    )

    term = BALL_ALPHA * raw
    return max(-BALL_TERM_CAP, min(BALL_TERM_CAP, term))


# ============================================================
# V8a-fast WEIGHT-CALIBRATION HELPERS
# ============================================================

def weight_centering_drag(current_w: float):
    if not ENABLE_WEIGHT_CALIBRATION:
        return 0.0

    mw = global_mean_weight_snapshot
    excess_global = mw - TARGET_MEAN_W

    if abs(excess_global) <= WEIGHT_TOL:
        return 0.0

    edge_excess = current_w - TARGET_MEAN_W

    if excess_global > 0:
        drag = WEIGHT_CENTER_ALPHA * excess_global * max(0.0, edge_excess)
    else:
        drag = 0.0

    return drag


def excess_weight_penalty(current_w: float):
    if not ENABLE_WEIGHT_CALIBRATION:
        return 0.0
    excess = max(0.0, current_w - (TARGET_MEAN_W + WEIGHT_TOL))
    return EXCESS_WEIGHT_ALPHA * excess


# ============================================================
# V9-A FAST BALL-COHERENCE HELPERS
# ============================================================

def bfs_ball_profile(center: int, r_max: int = V9_R_MAX):
    """
    Returns:
      dist: node -> distance
      first_branch: node -> first neighbor from center along BFS tree
      shells: dict radius -> set of nodes at exact radius
    """
    neigh0 = list(active_undirected_neighbors(center))
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
        for v in active_undirected_neighbors(u):
            if v not in dist:
                dist[v] = d + 1
                first_branch[v] = first_branch[u]
                shells.setdefault(d + 1, set()).add(v)
                q.append((v, d + 1))

    for r in range(r_max + 1):
        shells.setdefault(r, set())

    return dist, first_branch, shells


def sector_balance_gain(i: int, center: int, first_branch: dict, shells: dict):
    """
    Coarse surrogate:
    If i's neighborhood reaches nodes that live in underfilled branches of center's
    radius-2/3 shells, reward it.
    """
    center_neighbors = list(active_undirected_neighbors(center))
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

    i_ball = local_two_hop_ball(i, radius=2)
    touched = 0
    for u in i_ball:
        b = first_branch.get(u, None)
        if b in underfilled:
            touched += 1

    return touched / max(1, len(i_ball))


def front_support_gain(i: int, shells: dict):
    """
    Reward if i brings reach toward outer shell r=3.
    """
    s2 = shells.get(2, set())
    s3 = shells.get(3, set())
    i_ball = local_two_hop_ball(i, radius=2)

    gain_r3 = len(i_ball - s3 - s2)
    overlap_inner = len(i_ball & s2)

    if gain_r3 + overlap_inner == 0:
        return 0.0
    return gain_r3 / (gain_r3 + overlap_inner)


def redundant_inner_overlap(i: int, shells: dict):
    s1 = shells.get(1, set())
    s2 = shells.get(2, set())
    i_ball = local_two_hop_ball(i, radius=2)

    inner_overlap = len(i_ball & (s1 | s2))
    total = len(i_ball)
    if total == 0:
        return 0.0
    return inner_overlap / total


def v9_ball_coherence_term(i: int, j: int):
    if not ENABLE_V9_BALL_COHERENCE:
        return 0.0
    if j < V9_MIN_NODE_AGE:
        return 0.0

    dist, first_branch, shells = bfs_ball_profile(j, r_max=V9_R_MAX)

    # Need at least some mesoscale structure
    if len(shells.get(2, set())) < 3:
        return 0.0

    novel_r2 = two_hop_coverage_gain(i, shells.get(1, set()) | shells.get(2, set()))
    novel_r3 = front_support_gain(i, shells)
    sec_gain = sector_balance_gain(i, j, first_branch, shells)
    red_inner = redundant_inner_overlap(i, shells)

    raw = (
        V9_W_R2 * novel_r2
        + V9_W_R3 * novel_r3
        + V9_W_SECTOR * sec_gain
        - V9_W_REDUNDANT * red_inner
    )

    # tiny front bonus if outer shell currently weak
    s2 = len(shells.get(2, set()))
    s3 = len(shells.get(3, set()))
    if s2 > 0:
        thin_front = max(0.0, (s2 - s3) / s2)
    else:
        thin_front = 0.0

    raw += V9_W_FRONT * thin_front * novel_r3

    term = V9_ALPHA * raw
    return max(-V9_TERM_CAP, min(V9_TERM_CAP, term))


# ============================================================
# PARENT SELECTION
# ============================================================

def choose_parents_for_new_node(m: int = M_PARENTS):
    if num_nodes <= 0:
        return []

    pool_size = min(CANDIDATE_POOL, num_nodes)
    candidate_ids = rng.choice(num_nodes, size=pool_size, replace=False).tolist()

    base_scores = {}
    sig_cache = {}

    for i in candidate_ids:
        ld = local_density_score(i)
        coh = float(node_coherence_ema[i])
        nov = novelty_score(i)
        base_scores[i] = math.exp(ALPHA * ld + BETA * coh + GAMMA * nov)

    chosen = []
    chosen_sigs = []

    while len(chosen) < min(m, len(candidate_ids)):
        remaining = [i for i in candidate_ids if i not in chosen]
        if not remaining:
            break

        scores = []
        for i in remaining:
            if i not in sig_cache:
                sig_cache[i] = ancestry_signature(i)

            repulsion_factor = 1.0
            for sig_p in chosen_sigs:
                sim = jaccard_sets(sig_cache[i], sig_p)
                repulsion_factor *= max(0.05, 1.0 - REPULSION_LAMBDA * sim)

            scores.append(base_scores[i] * repulsion_factor)

        pick = weighted_choice(remaining, scores)
        if pick is None:
            break

        chosen.append(pick)
        chosen_sigs.append(sig_cache[pick])

    return chosen


# ============================================================
# NODE RELAXATION
# ============================================================

def recompute_node_state(j: int) -> int:
    total = 0.0
    cnt = 0
    for eid in in_edges[j]:
        if not active[eid]:
            continue
        total += w[eid] * float(state[src[eid]])
        cnt += 1
    if cnt == 0:
        return int(state[j])
    avg = total / cnt
    return 1 if avg >= 0.5 else 0


def relax_random_nodes(batch_size: int = NODE_RELAX_BATCH):
    if num_nodes <= 1:
        return
    batch_size = min(batch_size, num_nodes - 1)
    nodes = rng.choice(np.arange(1, num_nodes), size=batch_size, replace=False)
    for j in nodes:
        state[j] = recompute_node_state(int(j))


# ============================================================
# UPDATE EDGE
# ============================================================

def update_edge(eid: int):
    global active_weight_sum

    if not active[eid]:
        return

    i = src[eid]
    j = dst[eid]
    old_w = w[eid]

    incoming = [pe for pe in in_edges[j] if active[pe]]
    m = len(incoming)

    coherence = 1.0 if state[i] == state[j] else 0.0

    if m <= 1:
        redundancy = 0.0
        mean_sim = 0.0
        conc_pressure = 0.0
        crowd_term = 0.0
        cluster_strength = 0.0
        sim_to_dom = 0.0
        drift_factor = 0.0
        membership = 0.0
    else:
        parent_nodes = [src[pe] for pe in incoming]
        sigs = [ancestry_signature(u) for u in parent_nodes]

        idx_e = incoming.index(eid)

        s_i = state[i]
        same = 0
        total_other = 0
        for idx, pe in enumerate(incoming):
            if idx == idx_e:
                continue
            total_other += 1
            if state[src[pe]] == s_i:
                same += 1
        redundancy = same / total_other if total_other > 0 else 0.0

        sim_mat = np.zeros((m, m), dtype=np.float64)
        q = np.ones(m, dtype=np.float64)

        crowd_load_arr = np.zeros(m, dtype=np.float64)
        cluster_load_arr = np.zeros(m, dtype=np.float64)

        for a in range(m):
            for b in range(a + 1, m):
                sim = jaccard_sets(sigs[a], sigs[b])
                sim_mat[a, b] = sim
                sim_mat[b, a] = sim
                q[a] += sim
                q[b] += sim

                if sim >= SIM_THRESHOLD:
                    excess = (sim - SIM_THRESHOLD) / (1.0 - SIM_THRESHOLD + 1e-12)
                    crowd_load_arr[a] += excess * w[incoming[b]]
                    crowd_load_arr[b] += excess * w[incoming[a]]

                if sim >= CROSS_SIM_THRESHOLD:
                    excess2 = (sim - CROSS_SIM_THRESHOLD) / (1.0 - CROSS_SIM_THRESHOLD + 1e-12)
                    cluster_load_arr[a] += excess2 * w[incoming[b]]
                    cluster_load_arr[b] += excess2 * w[incoming[a]]

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
            crowd_term = 0.0
            drift_factor = 0.0
            membership = 0.0
        else:
            p_crowd = crowd_load_arr / crowd_total
            C_j = float(np.sum(p_crowd * p_crowd))
            adaptive_factor = 1.0 + ADAPTIVE_ALPHA * max(0.0, C_j - C_TARGET)
            crowd_term = LAMBDA_CROWD * adaptive_factor * float(crowd_load_arr[idx_e])

            drift_factor = max(0.0, C_j - DRIFT_THRESHOLD) / max(1e-12, 1.0 - DRIFT_THRESHOLD)
            dom_idx_drift = int(np.argmax(p_crowd))
            membership = float(sim_mat[idx_e, dom_idx_drift])

        cluster_total = float(np.sum(cluster_load_arr))
        if cluster_total <= 1e-12:
            cluster_strength = 0.0
            sim_to_dom = 0.0
        else:
            p_cluster = cluster_load_arr / cluster_total
            dom_idx = int(np.argmax(p_cluster))
            cluster_strength = float(np.max(p_cluster))
            sim_to_dom = float(sim_mat[idx_e, dom_idx])

    density_p = density_pressure(float(active_in_degree[j]))
    inhib = INHIB_GAMMA * mean_sim * (1.0 + CONC_GAMMA * conc_pressure) * (1.0 + density_p)

    # load saturation
    sum_in = 0.0
    for pe in in_edges[j]:
        if active[pe]:
            sum_in += w[pe]

    sum_out = 0.0
    for pe in out_edges[i]:
        if active[pe]:
            sum_out += w[pe]

    share_in = old_w / (sum_in + LOAD_EPS)
    share_out = old_w / (sum_out + LOAD_EPS)
    load_proxy = 0.5 * share_in + 0.5 * share_out

    reward_term = ETA * (2.0 * coherence - 1.0) / (1.0 + LOAD_BETA * load_proxy)
    load_drag = LOAD_GAMMA * (load_proxy ** 2)

    # topological outflow gate
    ni = active_undirected_neighbors(i)
    nj = active_undirected_neighbors(j)
    shared_frac = shared_neighbor_fraction_from_sets(ni, nj)

    loop_gate = max(0.0, 1.0 - shared_frac / max(MAX_SHARED_NEIGHBOR_FRAC, 1e-12))
    loop_gate = min(1.0, loop_gate)

    deg_i = len(ni)
    deg_j = len(nj)
    if deg_i <= 0:
        sparse_gate = 1.0
    else:
        ratio = (deg_i - deg_j) / max(1.0, deg_i)
        sparse_gate = 1.0 / (1.0 + math.exp(-OUTFLOW_BETA * ratio))
        sparse_gate = max(0.0, min(1.0, sparse_gate))

    gate = loop_gate * sparse_gate

    active_cluster = max(0.0, cluster_strength - CROSS_MIN_CLUSTER_WEIGHT)
    genealogical_novelty = (1.0 - sim_to_dom) ** GENEALOGICAL_NOVELTY_BETA

    cross_bonus = (
        CROSS_ALPHA
        * active_cluster
        * genealogical_novelty
        * (1.0 - min(1.0, load_proxy))
        * gate
    )

    # plasticity
    age = current_step - edge_birth[eid]
    if PLASTICITY_ONLY_ON_OLD and age < OLD_EDGE_AGE:
        plastic_term = 0.0
    else:
        age_fac = 1.0 - math.exp(-age / AGE_TAU)
        plastic_term = min(PLASTICITY_CAP, AGE_ALPHA * age_fac * drift_factor * membership)

    # V8a-fast contrast
    ball_term = ball_integrity_term(i, j)

    # V9-A new mesoscale contrast
    v9_term = v9_ball_coherence_term(i, j)

    # calibration
    center_drag = weight_centering_drag(old_w)
    excess_pen = excess_weight_penalty(old_w)

    new_w = (
        old_w
        + reward_term
        + cross_bonus
        + ball_term
        + v9_term
        - NU * redundancy
        - inhib
        - crowd_term
        - load_drag
        - plastic_term
        - center_drag
        - excess_pen
        - MU * (old_w - W0)
    )

    if new_w < effective_wmin(j):
        deactivate_edge(eid)
        return

    final_w = float(min(W_MAX, max(new_w, W_MIN)))
    w[eid] = final_w
    active_weight_sum += (final_w - old_w)

    node_coherence_ema[i] = 0.98 * node_coherence_ema[i] + 0.02 * coherence


def update_random_edges(batch_size: int = EDGE_UPDATE_BATCH):
    n = len(active_edge_ids)
    if n == 0:
        return
    batch_size = min(batch_size, n)
    idxs = rng.choice(n, size=batch_size, replace=False)
    picked_eids = [active_edge_ids[int(k)] for k in idxs]
    for eid in picked_eids:
        if active[eid]:
            update_edge(eid)


# ============================================================
# GROWTH STEP
# ============================================================

def infer_new_node_level(parents):
    if not parents:
        return 0
    return 1 + int(max(node_level[p] for p in parents))


def grow_one_step():
    global current_step, global_mean_weight_snapshot
    current_step += 1
    global_mean_weight_snapshot = current_mean_weight()

    parents = choose_parents_for_new_node(M_PARENTS)

    if parents:
        avg = np.mean([state[p] for p in parents])
        s_new = 1 if avg >= 0.5 else 0
    else:
        s_new = int(rng.integers(0, 2))

    lvl_new = infer_new_node_level(parents)
    j = add_node(int(s_new), lvl_new)

    new_eids = []
    for p in parents:
        new_eids.append(add_edge(p, j, W0))

    for eid in new_eids:
        update_edge(eid)

    state[j] = recompute_node_state(j)
    relax_random_nodes(NODE_RELAX_BATCH)
    update_random_edges(EDGE_UPDATE_BATCH)


# ============================================================
# GENERIC GRAPH / DIFFUSION HELPERS
# ============================================================

def build_shadow_adjacency(region_nodes):
    region_set = set(region_nodes)
    neigh = {u: set() for u in region_nodes}
    for eid in active_edge_ids:
        i = src[eid]
        j = dst[eid]
        if i in region_set and j in region_set:
            neigh[i].add(j)
            neigh[j].add(i)
    return neigh


def estimate_return_probabilities(neigh, taus, n_walkers, start_nodes=None):
    valid_nodes = [u for u, nbrs in neigh.items() if len(nbrs) > 0]
    if not valid_nodes:
        return {tau: 0.0 for tau in taus}

    if start_nodes is None:
        starts_pool = valid_nodes
    else:
        starts_pool = [u for u in start_nodes if u in neigh and len(neigh[u]) > 0]

    if not starts_pool:
        return {tau: 0.0 for tau in taus}

    taus = sorted(taus)
    tau_set = set(taus)
    max_tau = taus[-1]
    returns = {tau: 0 for tau in taus}

    starts = rng.choice(starts_pool, size=n_walkers, replace=True)
    for start in starts:
        cur = int(start)
        for t in range(1, max_tau + 1):
            nbrs = tuple(neigh[cur])
            if not nbrs:
                break
            cur = nbrs[int(rng.integers(0, len(nbrs)))]
            if t in tau_set and cur == start:
                returns[t] += 1

    return {tau: returns[tau] / n_walkers for tau in taus}


def estimate_spectral_dimension(ret_probs, taus):
    ds_pairs = []
    for a, b in zip(taus[:-1], taus[1:]):
        pa = ret_probs.get(a, 0.0)
        pb = ret_probs.get(b, 0.0)
        if pa > 0.0 and pb > 0.0 and pb < pa:
            ds = -2.0 * math.log(pb / pa) / math.log(b / a)
            ds_pairs.append(ds)
    if not ds_pairs:
        return None, []
    return float(np.mean(ds_pairs)), ds_pairs


def estimate_volume_growth_dimension(neigh, region_nodes):
    if not region_nodes:
        return None

    center = int(rng.choice(region_nodes))
    q = deque([(center, 0)])
    dist = {center: 0}

    while q:
        u, d = q.popleft()
        for v in neigh[u]:
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


def bfs_distance(neigh, start, goal):
    if start == goal:
        return 0
    q = deque([start])
    dist = {start: 0}
    while q:
        u = q.popleft()
        du = dist[u]
        for v in neigh[u]:
            if v == goal:
                return du + 1
            if v not in dist:
                dist[v] = du + 1
                q.append(v)
    return None


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


def rank_quantile_partition_from_dist(dist_map, core_frac=K6_CORE_FRAC, mid_frac=K6_MID_FRAC):
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


def start_class_ds(full_neigh, start_nodes, taus, n_walkers, min_start_nodes=K6_MIN_START_NODES):
    valid_starts = [u for u in start_nodes if u in full_neigh and len(full_neigh[u]) > 0]
    if len(valid_starts) < min_start_nodes:
        return None, None, None
    ret_probs = estimate_return_probabilities(full_neigh, taus, n_walkers, start_nodes=valid_starts)
    ds_est, ds_pairs = estimate_spectral_dimension(ret_probs, taus)
    return ds_est, ds_pairs, ret_probs


# ============================================================
# K1 STORAGE
# ============================================================

observables_k1 = []
observables_k2_global = []
observables_k4_global = []
observables_k5_global = []
observables_k7 = []


# ============================================================
# K1
# ============================================================

def record_observables(step: int):
    ws = active_weights_np()
    if ws.size == 0:
        return

    deg = active_out_degree[:num_nodes].astype(np.float64)
    mean_k = float(np.mean(deg))
    var_k = float(np.var(deg))

    counts = Counter(deg.astype(int))
    probs = np.array(list(counts.values()), dtype=np.float64)
    probs = probs / probs.sum()
    H = float(-np.sum(probs * np.log(probs + 1e-12)) / math.log(len(probs) + 1e-12))

    obs = {
        "step": step,
        "num_nodes": num_nodes,
        "num_edges_total": len(src),
        "num_edges_active": len(active_edge_ids),
        "mean_weight": float(np.mean(ws)),
        "std_weight": float(np.std(ws)),
        "min_weight": float(np.min(ws)),
        "max_weight": float(np.max(ws)),
        "frac_near_wmin": float(np.mean(ws <= (W_MIN + 0.05))),
        "frac_near_wmax": float(np.mean(ws >= (W_MAX - 0.10))),
        "mean_k_out": mean_k,
        "var_k_out": var_k,
        "H_degree": H,
    }
    observables_k1.append(obs)

    print(
        f"step={step:5d} "
        f"nodes={num_nodes:5d} "
        f"active_edges={len(active_edge_ids):6d} "
        f"mean_w={obs['mean_weight']:.3f} "
        f"std_w={obs['std_weight']:.3f} "
        f"min_w={obs['min_weight']:.3f} "
        f"max_w={obs['max_weight']:.3f} "
        f"near_min={obs['frac_near_wmin']:.3f} "
        f"near_max={obs['frac_near_wmax']:.3f} "
        f"mean_k={obs['mean_k_out']:.3f} "
        f"var_k={obs['var_k_out']:.3f} "
        f"H={obs['H_degree']:.4f}"
    )


# ============================================================
# ANCHOR SETUP
# ============================================================

def sample_bfs_region_from_seed(seed: int, target_size: int):
    if seed >= num_nodes:
        return []

    q = deque([seed])
    seen = {seed}
    region = [seed]

    while q and len(region) < target_size:
        u = q.popleft()
        nbrs = []

        for eid in out_edges[u]:
            if active[eid]:
                nbrs.append(dst[eid])
        for eid in in_edges[u]:
            if active[eid]:
                nbrs.append(src[eid])

        rng.shuffle(nbrs)
        for v in nbrs:
            if v not in seen and v < num_nodes:
                seen.add(v)
                q.append(v)
                region.append(v)
                if len(region) >= target_size:
                    break

    return region


def initialize_anchors():
    candidates = list(range(num_nodes))
    rng.shuffle(candidates)

    seeds = []
    for u in candidates:
        if len(seeds) >= NUM_ANCHORS:
            break
        ok = True
        for s in seeds:
            if abs(u - s) < 2:
                ok = False
                break
        if ok:
            seeds.append(u)

    anchors = []
    for aid, seed in enumerate(seeds):
        anchors.append({
            "anchor_id": aid,
            "seed": int(seed),
        })
    return anchors


# ============================================================
# GLOBAL K2/K4/K5 OPTIONAL
# ============================================================

def sample_bfs_region(target_size: int):
    if num_nodes == 0:
        return []
    start = int(rng.integers(0, num_nodes))
    return sample_bfs_region_from_seed(start, target_size)


def measure_k2_global(step: int):
    region = sample_bfs_region(K2_REGION_SIZE)
    if len(region) < 50:
        return

    neigh = build_shadow_adjacency(region)
    mean_shadow_deg = float(np.mean([len(neigh[u]) for u in region]))

    ret_probs = estimate_return_probabilities(neigh, K2_TAUS, K2_WALKERS)
    ds_est, ds_pairs = estimate_spectral_dimension(ret_probs, K2_TAUS)
    dv_est = estimate_volume_growth_dimension(neigh, region)

    obs = {
        "step": step,
        "num_region_nodes": len(region),
        "region_fraction": len(region) / num_nodes,
        "shadow_mean_degree": mean_shadow_deg,
        "return_probs": ret_probs,
        "ds_est": ds_est,
        "ds_pairs": ds_pairs,
        "dv_est": dv_est,
    }
    observables_k2_global.append(obs)

    ptxt = " ".join([f"P{tau}={ret_probs[tau]:.4f}" for tau in K2_TAUS])
    print(
        f"K2-global step={step:5d} "
        f"region_nodes={len(region)} "
        f"region_frac={len(region)/num_nodes:.4f} "
        f"shadow_deg={mean_shadow_deg:.3f} "
        f"{ptxt} "
        f"ds~={ds_est if ds_est is not None else 'nan'} "
        f"dv~={dv_est if dv_est is not None else 'nan'}"
    )


def measure_k4_global(step: int):
    region = sample_bfs_region(K2_REGION_SIZE)
    if len(region) < 50:
        return

    neigh = build_shadow_adjacency(region)

    herf_vals = []
    for j in region:
        incoming = [pe for pe in in_edges[j] if active[pe]]
        if len(incoming) <= 1:
            continue
        ws = np.array([w[pe] for pe in incoming], dtype=np.float64)
        s = ws.sum()
        if s <= 0:
            continue
        p = ws / s
        herf_vals.append(float(np.sum(p * p)))

    mean_herf = float(np.mean(herf_vals)) if herf_vals else None
    q90_herf = float(np.quantile(herf_vals, 0.9)) if herf_vals else None

    cluster_doms = []
    for j in region:
        incoming = [pe for pe in in_edges[j] if active[pe]]
        m = len(incoming)
        if m <= 1:
            continue

        parent_nodes = [src[pe] for pe in incoming]
        sigs = [ancestry_signature(u) for u in parent_nodes]
        cluster_load = np.zeros(m, dtype=np.float64)

        for a in range(m):
            for b in range(a + 1, m):
                sim = jaccard_sets(sigs[a], sigs[b])
                if sim >= CROSS_SIM_THRESHOLD:
                    excess = (sim - CROSS_SIM_THRESHOLD) / (1.0 - CROSS_SIM_THRESHOLD + 1e-12)
                    cluster_load[a] += excess * w[incoming[b]]
                    cluster_load[b] += excess * w[incoming[a]]

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
        pair_count = min(K4_PAIR_SAMPLES, len(valid_nodes) * (len(valid_nodes) - 1) // 2)
        for _ in range(pair_count):
            a, b = rng.choice(valid_nodes, size=2, replace=False)
            d = bfs_distance(neigh, int(a), int(b))
            if d is None:
                effs.append(0.0)
            else:
                dists.append(d)
                effs.append(1.0 / d if d > 0 else 0.0)

    mean_eff = float(np.mean(effs)) if effs else None
    mean_path = float(np.mean(dists)) if dists else None

    obs = {
        "step": step,
        "region_nodes": len(region),
        "region_fraction": len(region) / num_nodes,
        "mean_in_herfindahl": mean_herf,
        "q90_in_herfindahl": q90_herf,
        "mean_cluster_dominance": mean_cluster_dom,
        "q90_cluster_dominance": q90_cluster_dom,
        "mean_global_efficiency": mean_eff,
        "mean_sample_path_length": mean_path,
    }
    observables_k4_global.append(obs)

    print(
        f"K4-global step={step:5d} "
        f"H_in={mean_herf if mean_herf is not None else 'nan'} "
        f"H90={q90_herf if q90_herf is not None else 'nan'} "
        f"C_dom={mean_cluster_dom if mean_cluster_dom is not None else 'nan'} "
        f"C90={q90_cluster_dom if q90_cluster_dom is not None else 'nan'} "
        f"Eff={mean_eff if mean_eff is not None else 'nan'} "
        f"L={mean_path if mean_path is not None else 'nan'}"
    )


def measure_k5_global(step: int):
    region = sample_bfs_region(K2_REGION_SIZE)
    if len(region) < 50:
        return

    neigh = build_shadow_adjacency(region)

    seed = int(rng.choice(region))
    shells, dist = shell_distribution_from_seed(neigh, seed)

    arr = np.array(shells, dtype=np.float64)
    total = arr.sum()
    if total <= 0:
        return
    p = arr / total
    shell_entropy = float(-np.sum(p * np.log(p + 1e-12)))
    radii = np.arange(len(arr), dtype=np.float64)
    mean_r = float(np.sum(radii * p))
    var_r = float(np.sum(((radii - mean_r) ** 2) * p))
    front_thickness = math.sqrt(max(0.0, var_r))
    peak_shell = int(np.argmax(arr))

    obs = {
        "step": step,
        "region_nodes": len(region),
        "region_fraction": len(region) / num_nodes,
        "shell_entropy": shell_entropy,
        "front_thickness": front_thickness,
        "peak_shell": peak_shell,
    }
    observables_k5_global.append(obs)

    print(
        f"K5-global step={step:5d} "
        f"S_shell={shell_entropy:.4f} "
        f"front_sigma={front_thickness:.4f} "
        f"peak_shell={peak_shell}"
    )


# ============================================================
# K7 ANCHOR MEASUREMENT
# ============================================================

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


def estimate_isotropy_defect(neigh, region_nodes, radii=K3_RADII, num_centers=K3_NUM_CENTERS):
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


def estimate_causal_front_proxy(region_nodes, num_seeds=K3_NUM_SEEDS, max_depth=K3_MAX_DEPTH):
    seeds = rng.choice(region_nodes, size=min(num_seeds, len(region_nodes)), replace=False)

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
            for eid in out_edges[u]:
                if not active[eid]:
                    continue
                v = dst[eid]
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


def measure_anchor(anchor, step):
    seed = anchor["seed"]
    if seed >= num_nodes:
        return None

    region_live = sample_bfs_region_from_seed(seed, ANCHOR_REGION_SIZE)

    if len(region_live) < ANCHOR_MIN_REGION:
        return None

    full_neigh = build_shadow_adjacency(region_live)

    if seed not in full_neigh or len(full_neigh[seed]) == 0:
        connected = [u for u in region_live if u in full_neigh and len(full_neigh[u]) > 0]
        if not connected:
            return None
        seed = connected[0]

    ret_probs = estimate_return_probabilities(full_neigh, K2_TAUS, K2_WALKERS)
    ds_global, ds_pairs = estimate_spectral_dimension(ret_probs, K2_TAUS)
    dv_global = estimate_volume_growth_dimension(full_neigh, region_live)
    shadow_deg = float(np.mean([len(full_neigh[u]) for u in region_live]))

    iso_defect, _ = estimate_isotropy_defect(full_neigh, region_live)
    causal = estimate_causal_front_proxy(region_live)

    shells, dist = shell_distribution_from_seed(full_neigh, seed)
    core, mid, front, core_max_d, front_min_d = rank_quantile_partition_from_dist(dist)

    ds_core, _, _ = start_class_ds(full_neigh, core, K6_TAUS, K6_WALKERS)
    ds_mid, _, _ = start_class_ds(full_neigh, mid, K6_TAUS, K6_WALKERS)
    ds_front, _, _ = start_class_ds(full_neigh, front, K6_TAUS, K6_WALKERS)

    g_fm = None if (ds_front is None or ds_mid is None) else (ds_front - ds_mid)
    g_mc = None if (ds_mid is None or ds_core is None) else (ds_mid - ds_core)
    g_fc = None if (ds_front is None or ds_core is None) else (ds_front - ds_core)

    return {
        "step": step,
        "anchor_id": anchor["anchor_id"],
        "seed": anchor["seed"],
        "seed_used": seed,
        "region_nodes": len(region_live),
        "region_fraction": len(region_live) / num_nodes,
        "shadow_mean_degree": shadow_deg,
        "return_probs": ret_probs,
        "ds_global": ds_global,
        "ds_pairs": ds_pairs,
        "dv_global": dv_global,
        "iso_defect": iso_defect,
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


def measure_k7(step, anchors):
    results = []
    for anchor in anchors:
        out = measure_anchor(anchor, step)
        if out is not None:
            results.append(out)
            observables_k7.append(out)

    print(f"K7-debug step={step:5d} valid_anchors={len(results)}/{len(anchors)}")

    if not results:
        return

    def mean_of(key):
        vals = [r[key] for r in results if r[key] is not None]
        if not vals:
            return None
        return float(np.mean(vals))

    print(
        f"K7 step={step:5d} "
        f"anchors={len(results)} "
        f"ds={mean_of('ds_global') if mean_of('ds_global') is not None else 'nan'} "
        f"dv={mean_of('dv_global') if mean_of('dv_global') is not None else 'nan'} "
        f"iso={mean_of('iso_defect') if mean_of('iso_defect') is not None else 'nan'} "
        f"ds_core={mean_of('ds_core') if mean_of('ds_core') is not None else 'nan'} "
        f"ds_mid={mean_of('ds_mid') if mean_of('ds_mid') is not None else 'nan'} "
        f"ds_front={mean_of('ds_front') if mean_of('ds_front') is not None else 'nan'} "
        f"g_fc={mean_of('g_fc') if mean_of('g_fc') is not None else 'nan'}"
    )


# ============================================================
# CADENCE
# ============================================================

def should_measure_anchor(step: int):
    if FINE_START <= step <= FINE_END:
        return (step % FINE_EVERY) == 0
    return (step % K7_EVERY) == 0


# ============================================================
# INITIALIZATION
# ============================================================

for _ in range(N0):
    add_node(int(rng.integers(0, 2)), level=0)

for j in range(1, N0):
    prev = list(range(j))
    m0 = min(M_PARENTS, len(prev))
    parents = rng.choice(prev, size=m0, replace=False)
    lvl = 1 + max(node_level[int(p)] for p in parents) if len(parents) > 0 else 0

    node_level[j] = lvl
    current_max_level = max(current_max_level, int(lvl))

    for p in parents:
        add_edge(int(p), j, W0)

for eid in list(active_edge_ids):
    update_edge(eid)

anchors = initialize_anchors()
print(f"Initialized {len(anchors)} anchors.")
print("Anchor seeds:", [a["seed"] for a in anchors])
print(
    f"ENABLE_BALL_INTEGRITY_CONTRAST={ENABLE_BALL_INTEGRITY_CONTRAST}, "
    f"BALL_ALPHA={BALL_ALPHA}, BALL_RADIUS={BALL_RADIUS}"
)
print(
    f"ENABLE_WEIGHT_CALIBRATION={ENABLE_WEIGHT_CALIBRATION}, "
    f"TARGET_MEAN_W={TARGET_MEAN_W}, "
    f"WEIGHT_CENTER_ALPHA={WEIGHT_CENTER_ALPHA}, "
    f"EXCESS_WEIGHT_ALPHA={EXCESS_WEIGHT_ALPHA}"
)
print(
    f"ENABLE_V9_BALL_COHERENCE={ENABLE_V9_BALL_COHERENCE}, "
    f"V9_ALPHA={V9_ALPHA}, V9_R_MAX={V9_R_MAX}"
)


# ============================================================
# MAIN LOOP
# ============================================================

for step in range(1, N_TOTAL + 1):
    grow_one_step()

    if step % MEASURE_EVERY == 0:
        record_observables(step)

    if step % K2_GLOBAL_EVERY == 0:
        measure_k2_global(step)

    if step % K4_MEASURE_EVERY == 0:
        measure_k4_global(step)

    if step % K5_MEASURE_EVERY == 0:
        measure_k5_global(step)

    if should_measure_anchor(step):
        measure_k7(step, anchors)

    if ENABLE_EARLY_STOP and len(observables_k1) >= 5:
        last = observables_k1[-1]
        if last["mean_k_out"] < 0.2:
            print("Early stop: graph collapsed.")
            break


# ============================================================
# FINAL REPORT
# ============================================================

print("\nRun completed without early failure.\n")

print("Final verdict:")
print("-> V9-A-fast ball-coherence + V8a-fast + K7 completed.\n")

print("Last 5 K1 observables:")
for obs in observables_k1[-5:]:
    print(obs)

print("\nLast 5 K2-global observables:")
for obs in observables_k2_global[-5:]:
    print(obs)

print("\nLast 5 K4-global observables:")
for obs in observables_k4_global[-5:]:
    print(obs)

print("\nLast 5 K5-global observables:")
for obs in observables_k5_global[-5:]:
    print(obs)

print("\nLast 10 K7 anchor observables:")
for obs in observables_k7[-10:]:
    print(obs)

print("\n=== Code Execution Successful ===")
