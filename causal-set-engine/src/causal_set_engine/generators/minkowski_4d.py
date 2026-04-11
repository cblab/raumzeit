"""4D Minkowski sprinkling generator for robustness checks."""

from __future__ import annotations

import random
from dataclasses import dataclass

from causal_set_engine.core.causal_set import CausalSet


@dataclass(frozen=True)
class Event4D:
    """Space-time event in 1+3 dimensions with c=1."""

    t: float
    x: float
    y: float
    z: float


def minkowski_precedes(a: Event4D, b: Event4D) -> bool:
    """Return whether ``a ≺ b`` in 4D Minkowski spacetime (c=1)."""
    dt = b.t - a.t
    dx = b.x - a.x
    dy = b.y - a.y
    dz = b.z - a.z
    return dt > 0.0 and (dt * dt) >= (dx * dx + dy * dy + dz * dz)


def generate_minkowski_4d(
    n: int,
    t_range: tuple[float, float] = (0.0, 1.0),
    x_range: tuple[float, float] = (-1.0, 1.0),
    y_range: tuple[float, float] = (-1.0, 1.0),
    z_range: tuple[float, float] = (-1.0, 1.0),
    seed: int | None = None,
) -> tuple[CausalSet, list[Event4D]]:
    """Generate ``n`` random events in a bounded 4D Minkowski region."""
    if n < 0:
        raise ValueError("n must be non-negative")

    rng = random.Random(seed)
    events = [
        Event4D(
            t=rng.uniform(t_range[0], t_range[1]),
            x=rng.uniform(x_range[0], x_range[1]),
            y=rng.uniform(y_range[0], y_range[1]),
            z=rng.uniform(z_range[0], z_range[1]),
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
