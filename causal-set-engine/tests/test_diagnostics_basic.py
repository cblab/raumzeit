"""Tests for basic diagnostics."""

from causal_set_engine.core.causal_set import CausalSet
from causal_set_engine.diagnostics.basic import (
    estimate_dimension_chain_height,
    longest_chain_between,
    sampled_interval_statistics,
)
from causal_set_engine.generators.minkowski_2d import generate_minkowski_2d
from causal_set_engine.generators.random_poset import generate_random_poset


def _mini_causet() -> CausalSet:
    """Build a small hand-checkable causal set.

    Relations:
      0 -> 1 -> 3 -> 4
      0 -> 2 -> 3 -> 4
    """
    cset = CausalSet()
    cset.add_relation(0, 1)
    cset.add_relation(0, 2)
    cset.add_relation(1, 3)
    cset.add_relation(2, 3)
    cset.add_relation(3, 4)
    return cset


def test_longest_chain_between_related_and_unrelated() -> None:
    cset = _mini_causet()

    assert longest_chain_between(cset, 0, 4) == 4
    assert longest_chain_between(cset, 1, 4) == 3
    assert longest_chain_between(cset, 1, 2) == 0


def test_sampled_interval_statistics_on_deterministic_pairs() -> None:
    cset = _mini_causet()
    stats = sampled_interval_statistics(cset, pairs=[(0, 3), (0, 4), (1, 2)])

    assert stats["requested_pairs"] == 3
    assert stats["used_pairs"] == 2
    assert stats["min"] == 2
    assert stats["max"] == 3
    assert stats["mean"] == 2.5
    assert stats["median"] == 2.5


def test_dimension_estimator_distinguishes_minkowski_from_null_model() -> None:
    n = 80
    seed = 21

    minkowski_cset, _ = generate_minkowski_2d(n=n, seed=seed)
    null_cset = generate_random_poset(n=n, relation_probability=0.2, seed=seed)

    d_minkowski = estimate_dimension_chain_height(minkowski_cset)
    d_null = estimate_dimension_chain_height(null_cset)

    assert d_minkowski > d_null + 0.6
