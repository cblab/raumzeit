"""Random poset null-model generator."""

from __future__ import annotations

import random

from causal_set_engine.core.causal_set import CausalSet


def generate_random_poset(
    n: int,
    relation_probability: float = 0.2,
    seed: int | None = None,
) -> CausalSet:
    """Generate a random DAG-based poset over ``n`` labeled elements.

    Construction uses a random linear extension induced by index ordering and
    samples forward edges with ``relation_probability``.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if not 0.0 <= relation_probability <= 1.0:
        raise ValueError("relation_probability must be in [0, 1]")

    rng = random.Random(seed)
    cset = CausalSet()
    for i in range(n):
        cset.add_element(i)

    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < relation_probability:
                cset.add_relation(i, j)

    return cset
