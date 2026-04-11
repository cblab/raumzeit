"""Myrheim-Meyer dimension estimator for finite causal sets.

The estimator uses the ordering fraction (comparable ordered-pair density)

    r = R / (N (N - 1))

where ``R`` is the number of ordered comparable pairs ``(x, y)`` with ``x ≺ y``
and ``N`` is cardinality. For Poisson sprinklings into an Alexandrov interval in
flat ``d``-dimensional Minkowski spacetime, the continuum expectation is

    E[r] = C(d) = Gamma(d + 1) * Gamma(d / 2) / (4 * Gamma(3 d / 2)).

This module estimates ``d`` by numerically inverting ``C(d)`` via a transparent
bisection solve over a fixed bracket.

Important assumptions/limits:
- calibrated for interval-like Minkowski references; non-interval regions and
  curved/non-manifold-like sets can bias the estimate,
- finite-size variance can be large at small ``N``,
- if ``r`` lies outside the bracketed model range, the solver returns the
  corresponding boundary dimension.
"""

from __future__ import annotations

import math

from causal_set_engine.core.causal_set import CausalSet
from causal_set_engine.diagnostics.basic import relation_density


def expected_ordering_fraction(dimension: float) -> float:
    """Return continuum ordering-fraction model ``C(d)`` for ``d >= 1``."""
    if dimension < 1.0:
        raise ValueError("dimension must be >= 1")
    return (
        math.gamma(dimension + 1.0)
        * math.gamma(dimension / 2.0)
        / (4.0 * math.gamma(1.5 * dimension))
    )


def estimate_myrheim_meyer_dimension(
    cset: CausalSet,
    *,
    min_dimension: float = 1.0,
    max_dimension: float = 20.0,
    iterations: int = 80,
) -> float:
    """Estimate effective dimension by inverting the Myrheim-Meyer relation.

    Args:
        cset: finite causal set.
        min_dimension: lower bisection bracket (inclusive).
        max_dimension: upper bisection bracket (inclusive).
        iterations: fixed bisection iterations for deterministic precision.

    Returns:
        Estimated effective dimension. For ``N < 2`` this returns ``0.0``.
    """
    if min_dimension < 1.0:
        raise ValueError("min_dimension must be >= 1")
    if max_dimension <= min_dimension:
        raise ValueError("max_dimension must be > min_dimension")
    if iterations <= 0:
        raise ValueError("iterations must be positive")

    if cset.cardinality() < 2:
        return 0.0

    ordering_fraction = relation_density(cset)

    model_at_min = expected_ordering_fraction(min_dimension)
    model_at_max = expected_ordering_fraction(max_dimension)

    if ordering_fraction >= model_at_min:
        return min_dimension
    if ordering_fraction <= model_at_max:
        return max_dimension

    lo = min_dimension
    hi = max_dimension
    for _ in range(iterations):
        mid = 0.5 * (lo + hi)
        model_mid = expected_ordering_fraction(mid)
        if model_mid > ordering_fraction:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)
