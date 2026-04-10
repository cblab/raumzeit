from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import numpy as np


@dataclass
class GraphState:
    # edge storage
    src: List[int] = field(default_factory=list)
    dst: List[int] = field(default_factory=list)
    w: List[float] = field(default_factory=list)
    active: List[bool] = field(default_factory=list)
    active_pos: List[int] = field(default_factory=list)
    edge_birth: List[int] = field(default_factory=list)

    active_edge_ids: List[int] = field(default_factory=list)

    # adjacency
    out_edges: List[List[int]] = field(default_factory=list)
    in_edges: List[List[int]] = field(default_factory=list)

    # node state
    state: np.ndarray | None = None
    node_coherence_ema: np.ndarray | None = None
    active_in_degree: np.ndarray | None = None
    active_out_degree: np.ndarray | None = None
    node_level: np.ndarray | None = None

    # metadata
    num_nodes: int = 0
    current_step: int = 0
    current_max_level: int = 0

    # fast weight accounting
    active_weight_sum: float = 0.0
    active_edge_count: int = 0
    global_mean_weight_snapshot: float = 1.0

    # random generator
    rng: np.random.Generator | None = None


def create_graph_state(config: dict) -> GraphState:
    max_nodes = int(config["max_nodes"])

    g = GraphState()
    g.out_edges = [[] for _ in range(max_nodes)]
    g.in_edges = [[] for _ in range(max_nodes)]

    g.state = np.zeros(max_nodes, dtype=np.int8)
    g.node_coherence_ema = np.full(max_nodes, 0.5, dtype=np.float64)
    g.active_in_degree = np.zeros(max_nodes, dtype=np.int32)
    g.active_out_degree = np.zeros(max_nodes, dtype=np.int32)
    g.node_level = np.zeros(max_nodes, dtype=np.int32)

    seed = int(config["seed"])
    g.rng = np.random.default_rng(seed)

    return g


def add_node(g: GraphState, s: int, level: int = 0) -> int:
    idx = g.num_nodes

    g.state[idx] = s
    g.node_coherence_ema[idx] = 0.5
    g.active_in_degree[idx] = 0
    g.active_out_degree[idx] = 0
    g.node_level[idx] = int(level)

    if level > g.current_max_level:
        g.current_max_level = int(level)

    g.num_nodes += 1
    return idx


def add_edge(g: GraphState, i: int, j: int, weight: float, current_step: int) -> int:
    eid = len(g.src)

    g.src.append(i)
    g.dst.append(j)
    g.w.append(float(weight))
    g.active.append(True)

    g.active_pos.append(len(g.active_edge_ids))
    g.active_edge_ids.append(eid)

    g.edge_birth.append(current_step)

    g.out_edges[i].append(eid)
    g.in_edges[j].append(eid)

    g.active_out_degree[i] += 1
    g.active_in_degree[j] += 1

    g.active_weight_sum += float(weight)
    g.active_edge_count += 1
    return eid


def deactivate_edge(g: GraphState, eid: int) -> None:
    if not g.active[eid]:
        return

    g.active_weight_sum -= g.w[eid]
    g.active_edge_count -= 1

    g.active[eid] = False

    i = g.src[eid]
    j = g.dst[eid]

    g.active_out_degree[i] -= 1
    g.active_in_degree[j] -= 1

    pos = g.active_pos[eid]
    last = g.active_edge_ids[-1]
    g.active_edge_ids[pos] = last
    g.active_pos[last] = pos
    g.active_edge_ids.pop()


def current_mean_weight(g: GraphState, default_w0: float) -> float:
    if g.active_edge_count <= 0:
        return default_w0
    return g.active_weight_sum / g.active_edge_count


def active_weights_np(g: GraphState) -> np.ndarray:
    if not g.active_edge_ids:
        return np.array([], dtype=np.float64)
    return np.fromiter((g.w[eid] for eid in g.active_edge_ids), dtype=np.float64)


def active_undirected_neighbors(g: GraphState, u: int) -> set[int]:
    nbrs: set[int] = set()

    for eid in g.out_edges[u]:
        if g.active[eid]:
            nbrs.add(g.dst[eid])

    for eid in g.in_edges[u]:
        if g.active[eid]:
            nbrs.add(g.src[eid])

    return nbrs


def local_shadow_degree(g: GraphState, u: int) -> int:
    return len(active_undirected_neighbors(g, u))


def shared_neighbor_fraction_from_sets(ni: set[int], nj: set[int]) -> float:
    if not ni and not nj:
        return 0.0
    inter = len(ni & nj)
    union = len(ni | nj)
    if union == 0:
        return 0.0
    return inter / union


def recompute_node_state(g: GraphState, j: int) -> int:
    total = 0.0
    cnt = 0

    for eid in g.in_edges[j]:
        if not g.active[eid]:
            continue
        total += g.w[eid] * float(g.state[g.src[eid]])
        cnt += 1

    if cnt == 0:
        return int(g.state[j])

    avg = total / cnt
    return 1 if avg >= 0.5 else 0


def infer_new_node_level(g: GraphState, parents: list[int]) -> int:
    if not parents:
        return 0
    return 1 + int(max(g.node_level[p] for p in parents))
