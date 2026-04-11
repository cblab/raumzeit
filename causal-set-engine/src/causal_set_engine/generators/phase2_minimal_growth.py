"""Minimal causal-set growth sandbox for phase-2a probing.

Single rule family:
- Sequential birth order only.
- On each birth i, sample direct links x -> i from existing x < i with
  fixed probability link_probability.

No weights, no local optimization terms, and no curvature/gravity layers.
"""

from __future__ import annotations

import random

from causal_set_engine.core.causal_set import CausalSet


def generate_minimal_growth_causal_set(
    n: int,
    link_probability: float,
    seed: int,
    initial_chain_length: int = 1,
) -> CausalSet:
    """Generate a causal set by simple forward-time stochastic growth."""

    if n < 1:
        raise ValueError("n must be >= 1")
    if not 0.0 <= link_probability <= 1.0:
        raise ValueError("link_probability must be in [0, 1]")
    if initial_chain_length < 1 or initial_chain_length > n:
        raise ValueError("initial_chain_length must be in [1, n]")

    rng = random.Random(seed)
    cset = CausalSet()

    for element in range(initial_chain_length):
        cset.add_element(element)
        if element > 0:
            cset.add_relation(element - 1, element)

    for new_element in range(initial_chain_length, n):
        cset.add_element(new_element)
        for older in range(new_element):
            if rng.random() < link_probability:
                cset.add_relation(older, new_element)

    return cset
