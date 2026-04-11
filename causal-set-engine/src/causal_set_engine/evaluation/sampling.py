"""Shared sampling and batch helpers for evaluation workflows."""

from __future__ import annotations

from collections.abc import Callable

from causal_set_engine.core.causal_set import CausalSet
from causal_set_engine.evaluation.metrics import MetricRow, run_once


GeneratorFn = Callable[[int, int], CausalSet]


def batch_rows(
    generator: GeneratorFn,
    n: int,
    runs: int,
    seed_start: int,
    interval_samples: int,
) -> list[MetricRow]:
    """Generate metric rows for a contiguous seed range."""
    rows: list[MetricRow] = []
    for seed in range(seed_start, seed_start + runs):
        rows.append(run_once(generator(n, seed), interval_samples, seed))
    return rows


def edge_count_from_density(n: int, density: float) -> int:
    """Convert direct-edge density to an integer edge count for size ``n``."""
    max_forward_edges = n * (n - 1) // 2
    return int(round(density * max_forward_edges))
