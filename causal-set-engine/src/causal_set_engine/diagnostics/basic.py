"""Basic diagnostics for phase-1 causal set calibration."""

from __future__ import annotations

from causal_set_engine.core.causal_set import CausalSet


def num_elements(cset: CausalSet) -> int:
    """Return number of elements."""
    return cset.cardinality()


def num_comparable_pairs(cset: CausalSet) -> int:
    """Return count of comparable ordered pairs (x, y) with x ≺ y."""
    n = 0
    elements = sorted(cset.elements)
    for x in elements:
        for y in elements:
            if x != y and cset.is_related(x, y):
                n += 1
    return n


def relation_density(cset: CausalSet) -> float:
    """Return comparable-pair density among all ordered distinct pairs."""
    n = cset.cardinality()
    if n < 2:
        return 0.0
    return num_comparable_pairs(cset) / (n * (n - 1))


def interval_size(cset: CausalSet, x: int, y: int) -> int:
    """Return cardinality of Alexandrov interval I(x, y)."""
    return len(cset.interval(x, y))


def longest_chain_length(cset: CausalSet) -> int:
    """Compute longest chain length using dynamic programming over closure DAG."""
    elements = sorted(cset.elements)
    if not elements:
        return 0

    dp: dict[int, int] = {x: 1 for x in elements}
    for x in elements:
        for y in elements:
            if cset.is_related(x, y):
                dp[y] = max(dp[y], dp[x] + 1)
    return max(dp.values())
