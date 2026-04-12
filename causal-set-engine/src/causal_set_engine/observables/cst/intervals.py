"""Global Alexandrov interval primitives for CST observables.

This module intentionally focuses on reusable, auditable interval structure:
- interval extraction,
- interval cardinality,
- link detection,
- global interval-abundance histograms.

It does not introduce local curvature proxies or any action-based observable.
"""

from __future__ import annotations

from causal_set_engine.core.causal_set import CausalSet


def interval_elements(cset: CausalSet, x: int, y: int) -> tuple[int, ...]:
    """Return the Alexandrov interval elements ``I(x, y) = {z | x ≺ z ≺ y}``.

    Deterministic return semantics:
    - returns a sorted tuple of element ids,
    - returns an empty tuple if ``x`` and ``y`` are not causally comparable as ``x ≺ y``.

    Complexity note:
    - delegates to transitive reachability checks through ``CausalSet.interval``;
      this is explicit and auditable but can be expensive for large ``N``.
    """
    return tuple(sorted(cset.interval(x, y)))


def interval_size(cset: CausalSet, x: int, y: int) -> int:
    """Return ``|I(x, y)|``, the number of strict interval elements between ``x`` and ``y``."""
    return len(interval_elements(cset, x, y))


def is_link(cset: CausalSet, x: int, y: int) -> bool:
    """Return ``True`` iff ``x ≺ y`` is a link relation.

    Link semantics in this layer:
    - ``x`` must causally precede ``y``, and
    - the strict Alexandrov interval must be empty: ``I(x, y) = ∅``.

    Equivalently, this identifies 0-element intervals (``N0`` intervals) among
    ordered comparable pairs.
    """
    return cset.is_related(x, y) and interval_size(cset, x, y) == 0


def compute_interval_abundances(cset: CausalSet, k_max: int = 5) -> dict[int, int]:
    """Count interval abundances for ordered comparable pairs up to ``k_max``.

    Counting semantics are explicit and conservative:
    - iterate all ordered pairs ``(x, y)`` of distinct elements,
    - count only pairs with ``x ≺ y``,
    - let ``k = |I(x, y)|``,
    - if ``0 <= k <= k_max``, increment histogram bin ``k``.

    The returned histogram always includes all bins ``0..k_max``.
    Pairs with ``k > k_max`` are intentionally excluded from the histogram;
    callers can tune ``k_max`` based on study scope.
    """
    if k_max < 0:
        raise ValueError("k_max must be non-negative")

    histogram: dict[int, int] = {k: 0 for k in range(k_max + 1)}
    elements = sorted(cset.elements)
    for x in elements:
        for y in elements:
            if x == y or not cset.is_related(x, y):
                continue
            size = interval_size(cset, x, y)
            if size <= k_max:
                histogram[size] += 1

    return histogram
