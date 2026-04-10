from __future__ import annotations

from .ancestry import Ancestry, register_node
from .graph_model import (
    GraphState,
    add_edge,
    add_node,
    current_mean_weight,
    infer_new_node_level,
    recompute_node_state,
)


def _sample_existing_node(g: GraphState) -> int:
    return int(g.rng.integers(0, g.num_nodes))


def initialize_graph(g: GraphState, ancestry: Ancestry, config: dict) -> None:
    init_nodes = int(config.get("init_nodes", 2))
    w0 = float(config.get("w0", 1.0))

    for _ in range(init_nodes):
        s = int(g.rng.integers(0, 2))
        node = add_node(g, s=s, level=0)
        register_node(ancestry, node_id=node, step=0, parents=[])

    # Ensure initial connectivity through a simple chain.
    for u in range(1, g.num_nodes):
        add_edge(g, i=u - 1, j=u, weight=w0, current_step=0)


def maybe_add_growth_node(g: GraphState, ancestry: Ancestry, config: dict) -> int | None:
    if g.num_nodes >= int(config["max_nodes"]):
        return None

    p_birth = float(config.get("p_birth", 0.25))
    if g.rng.random() >= p_birth:
        return None

    if g.num_nodes == 0:
        return None

    p1 = _sample_existing_node(g)
    p2 = _sample_existing_node(g)
    parents = sorted(set([p1, p2]))

    level = infer_new_node_level(g, parents)
    s = int(g.rng.integers(0, 2))
    new_node = add_node(g, s=s, level=level)
    register_node(ancestry, node_id=new_node, step=g.current_step, parents=parents)

    mean_w = current_mean_weight(g, default_w0=float(config.get("w0", 1.0)))
    for p in parents:
        add_edge(g, i=p, j=new_node, weight=mean_w, current_step=g.current_step)

    return new_node


def maybe_add_random_edge(g: GraphState, config: dict) -> int | None:
    if g.num_nodes < 2:
        return None

    p_link = float(config.get("p_link", 0.4))
    if g.rng.random() >= p_link:
        return None

    i = _sample_existing_node(g)
    j = _sample_existing_node(g)
    if i == j:
        return None

    noise = float(config.get("w_noise", 0.05))
    mean_w = current_mean_weight(g, default_w0=float(config.get("w0", 1.0)))
    w = max(0.0, mean_w + float(g.rng.normal(0.0, noise)))

    return add_edge(g, i=i, j=j, weight=w, current_step=g.current_step)


def update_node_states(g: GraphState, config: dict) -> None:
    if g.num_nodes == 0:
        return

    frac = float(config.get("state_update_fraction", 0.5))
    k = max(1, int(round(frac * g.num_nodes)))
    chosen = g.rng.choice(g.num_nodes, size=min(k, g.num_nodes), replace=False)

    for j in chosen:
        new_s = recompute_node_state(g, int(j))
        old_s = int(g.state[j])
        g.state[j] = new_s

        # coherence = agreement of consecutive state updates (EMA-smoothed)
        agree = 1.0 if new_s == old_s else 0.0
        g.node_coherence_ema[j] = 0.9 * g.node_coherence_ema[j] + 0.1 * agree


def step(g: GraphState, ancestry: Ancestry, config: dict) -> None:
    g.current_step += 1
    maybe_add_growth_node(g, ancestry, config)
    maybe_add_random_edge(g, config)
    update_node_states(g, config)

    g.global_mean_weight_snapshot = current_mean_weight(g, default_w0=float(config.get("w0", 1.0)))
