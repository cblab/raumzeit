"""Basic diagnostics for causal set calibration.

These diagnostics stay deliberately simple for the diagnostic demo and reusable checks:
- they operate on finite causal sets with pure-Python algorithms,
- they avoid introducing new dynamics or theory layers,
- they provide first-pass reconstruction/calibration signals.
"""

from __future__ import annotations

import math
import random
import statistics
from collections.abc import Iterable

from causal_set_engine.core.causal_set import CausalSet


Pair = tuple[int, int]


def num_elements(cset: CausalSet) -> int:
    """Return number of elements."""
    return cset.cardinality()


def num_comparable_pairs(cset: CausalSet) -> int:
    """Return count of comparable ordered pairs ``(x, y)`` with ``x ≺ y``."""
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
    """Return cardinality of Alexandrov interval ``I(x, y)``."""
    return len(cset.interval(x, y))


def _topological_order(cset: CausalSet, subset: set[int]) -> list[int]:
    """Return a topological order of the induced direct-relation subgraph."""
    adjacency = {x: set() for x in subset}
    indegree = {x: 0 for x in subset}

    for x, futures in cset.direct_relations.items():
        if x not in subset:
            continue
        for y in futures:
            if y in subset:
                adjacency[x].add(y)
                indegree[y] += 1

    queue = sorted([x for x, d in indegree.items() if d == 0])
    order: list[int] = []
    while queue:
        x = queue.pop(0)
        order.append(x)
        for y in sorted(adjacency[x]):
            indegree[y] -= 1
            if indegree[y] == 0:
                queue.append(y)

    if len(order) != len(subset):
        raise ValueError("Expected a DAG in causal set induced subgraph.")
    return order


def longest_chain_between(cset: CausalSet, x: int, y: int) -> int:
    """Return longest chain length between related elements ``x ≺ y``.

    The returned length counts both endpoints, so a direct relation has length 2.
    If ``x`` and ``y`` are not related, the function returns 0.
    """
    if not cset.is_related(x, y):
        return 0

    subset = cset.interval(x, y) | {x, y}
    order = _topological_order(cset, subset)

    neg_inf = -10**9
    dp = {node: neg_inf for node in subset}
    dp[x] = 1

    adjacency = {
        node: {nxt for nxt in cset.direct_relations.get(node, set()) if nxt in subset}
        for node in subset
    }

    for node in order:
        if dp[node] == neg_inf:
            continue
        for nxt in adjacency[node]:
            dp[nxt] = max(dp[nxt], dp[node] + 1)

    return max(0, dp[y])


def longest_chain_length(cset: CausalSet) -> int:
    """Compute longest chain length of the entire causal set.

    Returns 0 for an empty causal set.
    """
    elements = cset.elements
    if not elements:
        return 0

    order = _topological_order(cset, elements)
    dp = {x: 1 for x in elements}

    for x in order:
        for y in cset.direct_relations.get(x, set()):
            dp[y] = max(dp[y], dp[x] + 1)

    return max(dp.values())


def sampled_interval_statistics(
    cset: CausalSet,
    pairs: int | Iterable[Pair],
    seed: int | None = None,
) -> dict[str, float | int | None]:
    """Return summary stats of interval sizes over sampled related pairs.

    Args:
        cset: causal set to inspect.
        pairs: either an integer sample count, or an iterable of candidate pairs.
            Non-related pairs are ignored.
        seed: random seed used only when ``pairs`` is an integer.
    """
    if isinstance(pairs, int):
        if pairs < 0:
            raise ValueError("pairs must be non-negative")
        related_pairs = [
            (x, y)
            for x in sorted(cset.elements)
            for y in sorted(cset.elements)
            if x != y and cset.is_related(x, y)
        ]
        rng = random.Random(seed)
        chosen = rng.sample(related_pairs, k=min(pairs, len(related_pairs)))
        requested = pairs
    else:
        chosen = list(pairs)
        requested = len(chosen)

    interval_sizes: list[int] = [
        interval_size(cset, x, y) for (x, y) in chosen if cset.is_related(x, y)
    ]

    if not interval_sizes:
        return {
            "requested_pairs": requested,
            "used_pairs": 0,
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
        }

    return {
        "requested_pairs": requested,
        "used_pairs": len(interval_sizes),
        "mean": float(statistics.fmean(interval_sizes)),
        "median": float(statistics.median(interval_sizes)),
        "min": min(interval_sizes),
        "max": max(interval_sizes),
    }


def estimate_dimension_chain_height(cset: CausalSet) -> float:
    """Estimate an effective dimension from chain-height scaling.

    Approximate estimator (explicitly approximate):
    assumes longest-chain growth approximately follows ``L ~ N^(1/d_eff)``;
    therefore ``d_eff ~= log(N) / log(L)``.

    This is intended only as a coarse calibration diagnostic and is most useful
    here for 2D-vs-non-2D discrimination, not for precision dimension recovery.
    """
    n = cset.cardinality()
    if n < 2:
        return 0.0

    l = longest_chain_length(cset)
    if l <= 1:
        return math.inf

    return math.log(float(n)) / math.log(float(l))
