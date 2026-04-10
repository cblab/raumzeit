from __future__ import annotations

from .ancestry import create_ancestry
from .diagnostics_k1 import measure_k1
from .diagnostics_k2 import measure_k2_global
from .graph_model import create_graph_state
from .updates import initialize_graph, step



def run_single(config: dict) -> dict:
    """Run one simulation and return a structured, JSON-serializable result."""

    g = create_graph_state(config)
    ancestry = create_ancestry(max_nodes=int(config["max_nodes"]))

    initialize_graph(g, ancestry, config)

    history = []
    history.append({"step": int(g.current_step), **measure_k1(g, config=config)})

    k2_every = int(config.get("k2_global_every", 0))
    observables_k2_global: list[dict] = []
    if k2_every > 0:
        observables_k2_global.append({"step": int(g.current_step), **measure_k2_global(g, config=config)})

    n_steps = int(config.get("steps", 0))
    for _ in range(n_steps):
        step(g, ancestry, config)
        history.append({"step": int(g.current_step), **measure_k1(g, config=config)})

        if k2_every > 0 and g.current_step % k2_every == 0:
            observables_k2_global.append({"step": int(g.current_step), **measure_k2_global(g, config=config)})

    return {
        "config": dict(config),
        "final": history[-1] if history else {},
        "history": history,
        "observables_k2_global": observables_k2_global,
        "graph": {
            "num_nodes": int(g.num_nodes),
            "num_edges_total": int(len(g.src)),
            "num_edges_active": int(g.active_edge_count),
            "max_level": int(g.current_max_level),
            "mean_weight_snapshot": float(g.global_mean_weight_snapshot),
        },
    }
