from __future__ import annotations

from .ancestry import create_ancestry
from .diagnostics_k1 import measure_k1
from .diagnostics_k2 import measure_k2_global
from .diagnostics_k7 import initialize_anchors, measure_k7
from .graph_model import create_graph_state
from .updates import initialize_graph, step


def run_single(config: dict) -> dict:
    """Run one simulation and return a structured, JSON-serializable result."""
    g = create_graph_state(config)
    ancestry = create_ancestry(max_nodes=int(config["max_nodes"]))

    initialize_graph(g, ancestry, config)

    history: list[dict] = []
    history.append({"step": int(g.current_step), **measure_k1(g, config=config)})

    k2_every = int(config.get("k2_global_every", 0))
    observables_k2_global: list[dict] = []
    if k2_every > 0:
        observables_k2_global.append({"step": int(g.current_step), **measure_k2_global(g, config=config)})

    k7_enabled = int(config.get("k7_every", 0)) > 0
    anchors = initialize_anchors(g, config) if k7_enabled else []
    observables_k7: list[dict] = []
    if k7_enabled:
        observables_k7.extend(measure_k7(step=int(g.current_step), g=g, anchors=anchors, config=config))

    n_steps = int(config.get("steps", 0))
    for _ in range(n_steps):
        step(g, ancestry, config)
        history.append({"step": int(g.current_step), **measure_k1(g, config=config)})

        if k2_every > 0 and g.current_step % k2_every == 0:
            observables_k2_global.append({"step": int(g.current_step), **measure_k2_global(g, config=config)})

        if k7_enabled:
            step_now = int(g.current_step)
            fine_start = int(config.get("fine_start", -1))
            fine_end = int(config.get("fine_end", -1))
            fine_every = int(config.get("fine_every", 0))
            k7_every = int(config.get("k7_every", 0))

            in_fine_window = fine_every > 0 and fine_start <= step_now <= fine_end
            cadence = fine_every if in_fine_window else k7_every

            if cadence > 0 and step_now % cadence == 0:
                observables_k7.extend(measure_k7(step=step_now, g=g, anchors=anchors, config=config))

    return {
        "config": dict(config),
        "final": history[-1] if history else {},
        "history": history,
        "observables_k2_global": observables_k2_global,
        "observables_k7": observables_k7,
        "graph": {
            "num_nodes": int(g.num_nodes),
            "num_edges_total": int(len(g.src)),
            "num_edges_active": int(g.active_edge_count),
            "max_level": int(g.current_max_level),
            "mean_weight_snapshot": float(g.global_mean_weight_snapshot),
        },
    }
