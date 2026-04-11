"""Additional conservative null models for phase-1.5 robustness checks."""

from __future__ import annotations

import random

from causal_set_engine.core.causal_set import CausalSet



def generate_fixed_edge_count_poset(
    n: int,
    edge_count: int,
    seed: int | None = None,
) -> CausalSet:
    """Generate a forward-DAG null model with exactly ``edge_count`` sampled edges.

    Preserves:
    - element count,
    - acyclicity via index-imposed forward ordering,
    - exact direct-edge count.

    Destroys:
    - Lorentzian lightcone constraints,
    - manifold-like interval geometry,
    - metric interpretation of coordinates.
    """
    if n < 0:
        raise ValueError("n must be non-negative")

    all_forward_edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    if edge_count < 0 or edge_count > len(all_forward_edges):
        raise ValueError("edge_count must lie in [0, n*(n-1)/2]")

    rng = random.Random(seed)
    sampled_edges = rng.sample(all_forward_edges, k=edge_count)

    cset = CausalSet()
    for i in range(n):
        cset.add_element(i)

    for i, j in sampled_edges:
        cset.add_relation(i, j)

    return cset
