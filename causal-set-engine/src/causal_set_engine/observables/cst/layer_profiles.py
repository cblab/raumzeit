"""Interval-internal layer-profile observables for CST analysis.

This module adds a conservative structural observable family defined inside one
Alexandrov interval ``(x, y)``.

Layering definition (version 1, deterministic):
- internal elements are the strict interval elements ``I(x, y) = {z | x ≺ z ≺ y}``,
- interval endpoints ``x`` and ``y`` are excluded from the profile,
- layer index starts at ``0``,
- an internal element ``z`` has layer index
  ``L(z) = 0`` if there is no internal predecessor ``w`` with ``x ≺ w ≺ z``,
  otherwise ``L(z) = 1 + max(L(w))`` over internal predecessors ``w``.

So the profile captures internal longest-chain depth from the lower endpoint, in
units of occupied internal layers.
"""

from __future__ import annotations

from dataclasses import dataclass

from causal_set_engine.core.causal_set import CausalSet
from causal_set_engine.observables.cst.intervals import interval_elements


@dataclass(frozen=True)
class LayerProfileSummary:
    """Simple derived summaries from one interval layer profile."""

    occupied_layer_count: int
    profile_height_index: int
    peak_layer_size: int
    peak_layer_index: int
    first_last_layer_fraction: float


def compute_interval_layer_assignments(cset: CausalSet, x: int, y: int) -> dict[int, int]:
    """Assign strict interval elements in ``I(x, y)`` to deterministic layer indices.

    Returns a mapping ``{element_id: layer_index}`` for internal elements only.
    If ``x`` and ``y`` are not comparable or if the strict interval is empty,
    returns an empty mapping.
    """
    internal = interval_elements(cset, x, y)
    if not internal:
        return {}

    internal_set = set(internal)
    assignments: dict[int, int] = {}

    def layer_index(z: int) -> int:
        if z in assignments:
            return assignments[z]
        predecessors = [w for w in internal_set if cset.is_related(w, z)]
        value = 0 if not predecessors else 1 + max(layer_index(w) for w in predecessors)
        assignments[z] = value
        return value

    for z in internal:
        layer_index(z)

    return assignments


def compute_layer_profile(cset: CausalSet, x: int, y: int) -> tuple[int, ...]:
    """Return the layer-count profile for one interval ``(x, y)``.

    The profile is a tuple indexed by layer index. Entry ``k`` is the count of
    internal interval elements with layer index ``k``.

    Height convention:
    - ``profile_height_index`` is the maximum occupied layer index,
    - number of occupied layers is ``profile_height_index + 1`` when non-empty.
    """
    assignments = compute_interval_layer_assignments(cset, x, y)
    if not assignments:
        return ()

    max_layer = max(assignments.values())
    counts = [0 for _ in range(max_layer + 1)]
    for layer_index in assignments.values():
        counts[layer_index] += 1
    return tuple(counts)


def summarize_layer_profile(profile: tuple[int, ...]) -> LayerProfileSummary:
    """Compute small, explicit summary statistics from a layer profile."""
    if not profile:
        return LayerProfileSummary(
            occupied_layer_count=0,
            profile_height_index=-1,
            peak_layer_size=0,
            peak_layer_index=-1,
            first_last_layer_fraction=0.0,
        )

    peak_size = max(profile)
    peak_index = next(idx for idx, count in enumerate(profile) if count == peak_size)
    total = sum(profile)
    boundary_mass = profile[0] if len(profile) == 1 else profile[0] + profile[-1]

    return LayerProfileSummary(
        occupied_layer_count=len(profile),
        profile_height_index=len(profile) - 1,
        peak_layer_size=peak_size,
        peak_layer_index=peak_index,
        first_last_layer_fraction=boundary_mass / total if total > 0 else 0.0,
    )


def compute_layer_profile_summary(cset: CausalSet, x: int, y: int) -> LayerProfileSummary:
    """Convenience wrapper to compute profile then its summary."""
    return summarize_layer_profile(compute_layer_profile(cset, x, y))
