"""Tests for CST midpoint-scaling primitives."""

from causal_set_engine.core.causal_set import CausalSet
from causal_set_engine.observables.cst.midpoint_scaling import (
    compute_midpoint_scaling_statistic,
    compute_subinterval_sizes,
    find_interval_midpoint,
    sampled_qualifying_intervals,
)


def _chain_cset(length: int) -> CausalSet:
    cset = CausalSet()
    for x in range(length):
        cset.add_element(x)
    for x in range(length - 1):
        cset.add_relation(x, x + 1)
    return cset


def test_find_interval_midpoint_chain_picks_most_balanced_candidate() -> None:
    cset = _chain_cset(5)
    assert find_interval_midpoint(cset, 0, 4) == 2


def test_find_interval_midpoint_tie_breaks_deterministically() -> None:
    cset = _chain_cset(6)
    # For interval (0, 5), z=2 and z=3 tie on asymmetry and support; pick smaller id.
    assert find_interval_midpoint(cset, 0, 5) == 2


def test_compute_subinterval_sizes_chain() -> None:
    cset = _chain_cset(5)
    assert compute_subinterval_sizes(cset, 0, 4, 2) == (1, 1)


def test_compute_midpoint_scaling_statistic_chain_is_explicit() -> None:
    cset = _chain_cset(5)
    stat = compute_midpoint_scaling_statistic(cset, 0, 4)

    assert stat.z == 2
    assert stat.interval_size_xy == 3
    assert stat.interval_size_xz == 1
    assert stat.interval_size_zy == 1
    assert stat.scaling_statistic == 5.0 / 3.0


def test_sampled_qualifying_intervals_reproducible_with_seed() -> None:
    cset = _chain_cset(8)

    sample_a = sampled_qualifying_intervals(
        cset,
        min_interval_size=3,
        max_sampled_intervals=4,
        seed=99,
    )
    sample_b = sampled_qualifying_intervals(
        cset,
        min_interval_size=3,
        max_sampled_intervals=4,
        seed=99,
    )

    assert sample_a == sample_b
    assert sample_a.sampled_interval_count == 4
    assert all(y - x - 1 >= 3 for x, y in sample_a.sampled_pairs)
