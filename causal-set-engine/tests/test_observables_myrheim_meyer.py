"""Tests for CST Myrheim-Meyer observable."""

from causal_set_engine.core.causal_set import CausalSet
from causal_set_engine.diagnostics.basic import relation_density
from causal_set_engine.generators.minkowski_2d import generate_minkowski_2d
from causal_set_engine.generators.minkowski_3d import generate_minkowski_3d
from causal_set_engine.generators.minkowski_4d import generate_minkowski_4d
from causal_set_engine.observables.cst.myrheim_meyer import (
    estimate_myrheim_meyer_dimension,
    expected_ordering_fraction,
)


def _total_order(n: int) -> CausalSet:
    cset = CausalSet()
    for i in range(n):
        cset.add_element(i)
    for i in range(n):
        for j in range(i + 1, n):
            cset.add_relation(i, j)
    return cset


def test_expected_ordering_fraction_matches_hand_checkable_values() -> None:
    assert abs(expected_ordering_fraction(1.0) - 0.5) < 1e-12
    assert abs(expected_ordering_fraction(2.0) - 0.25) < 1e-12
    assert abs(expected_ordering_fraction(4.0) - 0.05) < 1e-12


def test_myrheim_meyer_estimator_recovers_total_order_dimension_one() -> None:
    cset = _total_order(5)
    assert relation_density(cset) == 0.5
    assert estimate_myrheim_meyer_dimension(cset) == 1.0


def test_myrheim_meyer_estimator_monotone_on_minkowski_references() -> None:
    n = 80
    seed = 17
    cset2, _ = generate_minkowski_2d(n=n, seed=seed)
    cset3, _ = generate_minkowski_3d(n=n, seed=seed)
    cset4, _ = generate_minkowski_4d(n=n, seed=seed)

    d2 = estimate_myrheim_meyer_dimension(cset2)
    d3 = estimate_myrheim_meyer_dimension(cset3)
    d4 = estimate_myrheim_meyer_dimension(cset4)

    assert d2 < d3 < d4
