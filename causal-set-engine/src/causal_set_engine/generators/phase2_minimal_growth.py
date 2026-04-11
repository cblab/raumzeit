"""Minimal causal-set growth sandbox for phase-2 probing.

Primitive rule families:
- bernoulli-forward: fixed forward-link probability baseline.
- sparse-forward: explicit low-density profile decaying with birth index.
- age-biased-forward: simple age preference (older/newer) when linking.
- window-forward: bounded lookback window with fixed link probability.

No weights, no local optimization terms, and no curvature/gravity layers.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from causal_set_engine.core.causal_set import CausalSet


@dataclass(frozen=True)
class PrimitiveDynamicsFamily:
    """Auditable metadata for a primitive dynamics family."""

    name: str
    parameters: tuple[str, ...]
    mechanism: str
    anticipated_artifact_risk: str


def generate_bernoulli_forward_growth_causal_set(
    n: int,
    link_probability: float,
    seed: int,
    initial_chain_length: int = 1,
) -> CausalSet:
    """Generate by fixed-probability forward links on every birth."""

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


def generate_minimal_growth_causal_set(
    n: int,
    link_probability: float,
    seed: int,
    initial_chain_length: int = 1,
) -> CausalSet:
    """Backward-compatible alias for the baseline family."""
    return generate_bernoulli_forward_growth_causal_set(
        n=n,
        link_probability=link_probability,
        seed=seed,
        initial_chain_length=initial_chain_length,
    )


def generate_sparse_forward_growth_causal_set(
    n: int,
    base_link_probability: float,
    seed: int,
    initial_chain_length: int = 1,
) -> CausalSet:
    """Generate with explicit low-density behavior as the set grows.

    Link probability at birth i is ``base_link_probability / i``.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    if not 0.0 <= base_link_probability <= 1.0:
        raise ValueError("base_link_probability must be in [0, 1]")
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
        local_probability = base_link_probability / float(max(1, new_element))
        for older in range(new_element):
            if rng.random() < local_probability:
                cset.add_relation(older, new_element)

    return cset


def generate_age_biased_growth_causal_set(
    n: int,
    link_probability: float,
    age_bias: str,
    seed: int,
    initial_chain_length: int = 1,
    age_bias_strength: float = 1.0,
) -> CausalSet:
    """Generate with explicit age preference for link targets.

    ``age_bias='older'`` scales selection by age rank (older favored).
    ``age_bias='newer'`` inversely scales by age rank (newer favored).
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    if not 0.0 <= link_probability <= 1.0:
        raise ValueError("link_probability must be in [0, 1]")
    if age_bias not in {"older", "newer"}:
        raise ValueError("age_bias must be 'older' or 'newer'")
    if initial_chain_length < 1 or initial_chain_length > n:
        raise ValueError("initial_chain_length must be in [1, n]")
    if not 0.0 <= age_bias_strength <= 1.0:
        raise ValueError("age_bias_strength must be in [0, 1]")

    rng = random.Random(seed)
    cset = CausalSet()

    for element in range(initial_chain_length):
        cset.add_element(element)
        if element > 0:
            cset.add_relation(element - 1, element)

    for new_element in range(initial_chain_length, n):
        cset.add_element(new_element)
        denom = float(max(1, new_element))
        for older in range(new_element):
            if age_bias == "older":
                raw_scale = float(new_element - older) / denom
            else:
                raw_scale = float(older + 1) / denom
            age_scale = (1.0 - age_bias_strength) + (age_bias_strength * raw_scale)
            if rng.random() < (link_probability * age_scale):
                cset.add_relation(older, new_element)

    return cset


def generate_window_forward_growth_causal_set(
    n: int,
    link_probability: float,
    lookback_window: int,
    seed: int,
    initial_chain_length: int = 1,
) -> CausalSet:
    """Generate with bounded lookback: links only from recent ancestors."""
    if n < 1:
        raise ValueError("n must be >= 1")
    if not 0.0 <= link_probability <= 1.0:
        raise ValueError("link_probability must be in [0, 1]")
    if lookback_window < 1:
        raise ValueError("lookback_window must be >= 1")
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
        start = max(0, new_element - lookback_window)
        for older in range(start, new_element):
            if rng.random() < link_probability:
                cset.add_relation(older, new_element)

    return cset


PRIMITIVE_DYNAMICS_FAMILIES: tuple[PrimitiveDynamicsFamily, ...] = (
    PrimitiveDynamicsFamily(
        name="bernoulli-forward",
        parameters=("link_probability",),
        mechanism="Each existing element independently links to the new birth with fixed probability.",
        anticipated_artifact_risk="Can over-concentrate around global edge-density artifacts and weak locality.",
    ),
    PrimitiveDynamicsFamily(
        name="sparse-forward",
        parameters=("base_link_probability",),
        mechanism="Per-birth link probability decays as 1/i, enforcing explicitly sparse growth at larger i.",
        anticipated_artifact_risk="May become too disconnected at larger N, inflating interval degeneracy.",
    ),
    PrimitiveDynamicsFamily(
        name="age-biased-forward",
        parameters=("link_probability", "age_bias", "age_bias_strength"),
        mechanism="Fixed Bernoulli links are scaled by an explicit older/newer preference factor.",
        anticipated_artifact_risk="Can create strong age-layering artifacts and chain-height distortions.",
    ),
    PrimitiveDynamicsFamily(
        name="window-forward",
        parameters=("link_probability", "lookback_window"),
        mechanism="Only the most recent lookback window is eligible to link to each new element.",
        anticipated_artifact_risk="Hard horizon cutoff can impose artificial local memory scales.",
    ),
)
