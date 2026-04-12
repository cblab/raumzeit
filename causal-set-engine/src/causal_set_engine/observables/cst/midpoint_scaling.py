"""Midpoint-scaling observable primitives built on Alexandrov intervals.

This module implements an explicit, conservative midpoint-scaling toolkit:
- deterministic midpoint candidate selection inside a chosen interval,
- sub-interval size extraction around a midpoint candidate,
- a primary midpoint-scaling statistic based on induced sub-interval sizes,
- deterministic sampled-interval evaluation utilities for workflows.

Scope limits:
- no local curvature interpretation,
- no action-based observable logic,
- no dynamics-family assumptions.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from causal_set_engine.core.causal_set import CausalSet
from causal_set_engine.observables.cst.intervals import interval_elements, interval_size


@dataclass(frozen=True)
class MidpointScalingStatistic:
    """Explicit midpoint-scaling measurement for one interval ``(x, y)``."""

    x: int
    y: int
    z: int
    interval_size_xy: int
    interval_size_xz: int
    interval_size_zy: int
    asymmetry: int
    scaling_statistic: float
    derived_dimension_estimate: float


@dataclass(frozen=True)
class MidpointSamplingSummary:
    """Deterministic sampled midpoint-scaling summary for one causal set."""

    qualifying_interval_count: int
    sampled_interval_count: int
    sampled_pairs: tuple[tuple[int, int], ...]


def compute_subinterval_sizes(cset: CausalSet, x: int, y: int, z: int) -> tuple[int, int]:
    """Return strict sub-interval sizes ``(|I(x, z)|, |I(z, y)|)``.

    Raises:
        ValueError: if ``x \\prec z \\prec y`` does not hold.
    """
    if not (cset.is_related(x, z) and cset.is_related(z, y)):
        raise ValueError("z must satisfy x ≺ z ≺ y")
    return interval_size(cset, x, z), interval_size(cset, z, y)


def find_interval_midpoint(cset: CausalSet, x: int, y: int) -> int:
    """Select a deterministic midpoint candidate ``z`` in ``I(x, y)``.

    Selection rule:
    1. Minimize strict sub-interval asymmetry ``||I(x,z)| - |I(z,y)||``.
    2. Tie-break toward larger balanced sub-interval support via ``max(min(a,b))``.
    3. Tie-break toward larger total strict support ``a + b``.
    4. Final deterministic tie-break: smallest element id ``z``.

    Raises:
        ValueError: if ``x`` and ``y`` are not comparable as ``x ≺ y`` or if
            the strict interval is empty.
    """
    if not cset.is_related(x, y):
        raise ValueError("x and y must satisfy x ≺ y")

    candidates = interval_elements(cset, x, y)
    if not candidates:
        raise ValueError("I(x, y) is empty; no midpoint candidate exists")

    ranked: list[tuple[tuple[int, int, int, int], int]] = []
    for z in candidates:
        size_xz, size_zy = compute_subinterval_sizes(cset, x, y, z)
        asymmetry = abs(size_xz - size_zy)
        rank_key = (asymmetry, -min(size_xz, size_zy), -(size_xz + size_zy), z)
        ranked.append((rank_key, z))

    ranked.sort(key=lambda item: item[0])
    return ranked[0][1]


def compute_midpoint_scaling_statistic(
    cset: CausalSet,
    x: int,
    y: int,
    z: int | None = None,
) -> MidpointScalingStatistic:
    """Compute the explicit midpoint-scaling statistic for one interval.

    Primary statistic (explicitly returned):

    ``S = N_xy / ((N_xz + N_zy)/2)``

    where
    - ``N_xy = |I(x, y)| + 2``,
    - ``N_xz = |I(x, z)| + 2``,
    - ``N_zy = |I(z, y)| + 2``.

    Using ``+2`` keeps each interval cardinality on an inclusive endpoint basis,
    avoiding divide-by-zero in tiny strict intervals while preserving an explicit
    cardinality-ratio interpretation.

    A derived estimate is also returned:
    ``d_hat = log2(S)``.
    This estimate is secondary and should be interpreted conservatively.
    """
    midpoint = find_interval_midpoint(cset, x, y) if z is None else z
    size_xy = interval_size(cset, x, y)
    size_xz, size_zy = compute_subinterval_sizes(cset, x, y, midpoint)
    asymmetry = abs(size_xz - size_zy)

    n_xy = size_xy + 2
    n_xz = size_xz + 2
    n_zy = size_zy + 2
    denominator = 0.5 * (n_xz + n_zy)

    scaling_statistic = n_xy / denominator
    derived_dimension = math.log(scaling_statistic, 2.0)

    return MidpointScalingStatistic(
        x=x,
        y=y,
        z=midpoint,
        interval_size_xy=size_xy,
        interval_size_xz=size_xz,
        interval_size_zy=size_zy,
        asymmetry=asymmetry,
        scaling_statistic=scaling_statistic,
        derived_dimension_estimate=derived_dimension,
    )


def estimate_midpoint_scaling_dimension(
    cset: CausalSet,
    x: int,
    y: int,
    z: int | None = None,
) -> float:
    """Return only the derived midpoint-scaling dimension estimate ``log2(S)``.

    This is a convenience wrapper around :func:`compute_midpoint_scaling_statistic`.
    It is intentionally documented as a derived estimate rather than the primary
    observable output.
    """
    return compute_midpoint_scaling_statistic(cset, x, y, z).derived_dimension_estimate


def sampled_qualifying_intervals(
    cset: CausalSet,
    *,
    min_interval_size: int,
    max_sampled_intervals: int,
    seed: int,
) -> MidpointSamplingSummary:
    """Select a deterministic sampled set of qualifying ordered intervals.

    Qualifying intervals are ordered comparable pairs ``(x, y)`` with
    ``|I(x, y)| >= min_interval_size``.

    Sampling is deterministic and reproducible via ``seed``.
    """
    if min_interval_size < 0:
        raise ValueError("min_interval_size must be non-negative")
    if max_sampled_intervals <= 0:
        raise ValueError("max_sampled_intervals must be positive")

    elements = sorted(cset.elements)
    qualifying: list[tuple[int, int]] = []
    for x in elements:
        for y in elements:
            if x == y or not cset.is_related(x, y):
                continue
            if interval_size(cset, x, y) >= min_interval_size:
                qualifying.append((x, y))

    rng = random.Random(seed)
    shuffled = list(qualifying)
    rng.shuffle(shuffled)
    sampled = tuple(sorted(shuffled[:max_sampled_intervals]))

    return MidpointSamplingSummary(
        qualifying_interval_count=len(qualifying),
        sampled_interval_count=len(sampled),
        sampled_pairs=sampled,
    )
