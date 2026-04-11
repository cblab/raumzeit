"""3D Minkowski sprinkling generator for phase-1.5 robustness checks."""

from __future__ import annotations

import random
from dataclasses import dataclass

from causal_set_engine.core.causal_set import CausalSet


@dataclass(frozen=True)
class Event3D:
    """Space-time event in 1+2 dimensions with c=1."""

    t: float
    x: float
    y: float


def minkowski_precedes(a: Event3D, b: Event3D) -> bool:
    """Return whether ``a ≺ b`` in 3D Minkowski spacetime (c=1)."""
    dt = b.t - a.t
    dx = b.x - a.x
    dy = b.y - a.y
    return dt > 0.0 and (dt * dt) >= (dx * dx + dy * dy)


def generate_minkowski_3d(
    n: int,
    t_range: tuple[float, float] = (0.0, 1.0),
    x_range: tuple[float, float] = (-1.0, 1.0),
    y_range: tuple[float, float] = (-1.0, 1.0),
    seed: int | None = None,
) -> tuple[CausalSet, list[Event3D]]:
    """Generate ``n`` random events in a bounded 3D Minkowski region."""
    if n < 0:
        raise ValueError("n must be non-negative")

    rng = random.Random(seed)
    events = [
        Event3D(
            t=rng.uniform(t_range[0], t_range[1]),
            x=rng.uniform(x_range[0], x_range[1]),
            y=rng.uniform(y_range[0], y_range[1]),
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
