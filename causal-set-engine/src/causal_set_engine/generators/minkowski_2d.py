"""2D Minkowski sprinkling generator for diagnostic calibration."""

from __future__ import annotations

import random
from dataclasses import dataclass

from causal_set_engine.core.causal_set import CausalSet


@dataclass(frozen=True)
class Event2D:
    """Space-time event in 1+1 dimensions with c=1."""

    t: float
    x: float


def minkowski_precedes(a: Event2D, b: Event2D) -> bool:
    """Return whether ``a ≺ b`` in 2D Minkowski spacetime (c=1)."""
    dt = b.t - a.t
    dx = b.x - a.x
    return dt > 0.0 and (dt * dt) >= (dx * dx)


def generate_minkowski_2d(
    n: int,
    t_range: tuple[float, float] = (0.0, 1.0),
    x_range: tuple[float, float] = (-1.0, 1.0),
    seed: int | None = None,
) -> tuple[CausalSet, list[Event2D]]:
    """Generate ``n`` random events in a bounded 2D Minkowski region."""
    if n < 0:
        raise ValueError("n must be non-negative")

    rng = random.Random(seed)
    events = [
        Event2D(
            t=rng.uniform(t_range[0], t_range[1]),
            x=rng.uniform(x_range[0], x_range[1]),
        )
        for _ in range(n)
    ]

    cset = CausalSet()
    for i in range(n):
        cset.add_element(i)

    for i, a in enumerate(events):
        for j, b in enumerate(events):
            if i == j:
                continue
            if minkowski_precedes(a, b):
                cset.add_relation(i, j)

    return cset, events
