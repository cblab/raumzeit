"""Tests for CST layer-profile observables."""

from causal_set_engine.core.causal_set import CausalSet
from causal_set_engine.observables.cst.layer_profiles import (
    compute_interval_layer_assignments,
    compute_layer_profile,
    summarize_layer_profile,
)


def _layered_cset() -> CausalSet:
    cset = CausalSet()
    for x in range(6):
        cset.add_element(x)
    cset.add_relation(0, 1)
    cset.add_relation(0, 2)
    cset.add_relation(1, 3)
    cset.add_relation(2, 3)
    cset.add_relation(3, 4)
    cset.add_relation(4, 5)
    return cset


def test_interval_layer_assignments_are_deterministic_on_hand_case() -> None:
    cset = _layered_cset()

    assignments = compute_interval_layer_assignments(cset, 0, 5)

    # Internal interval elements are 1,2,3,4.
    # Layers by longest internal predecessor depth from x=0:
    # 1->0, 2->0, 3->1, 4->2
    assert assignments == {1: 0, 2: 0, 3: 1, 4: 2}


def test_layer_profile_counts_match_assignments() -> None:
    cset = _layered_cset()

    profile = compute_layer_profile(cset, 0, 5)

    assert profile == (2, 1, 1)


def test_layer_profile_summary_exposes_basic_shape() -> None:
    summary = summarize_layer_profile((2, 1, 1))

    assert summary.occupied_layer_count == 3
    assert summary.profile_height_index == 2
    assert summary.peak_layer_size == 2
    assert summary.peak_layer_index == 0
    assert summary.first_last_layer_fraction == 0.75
