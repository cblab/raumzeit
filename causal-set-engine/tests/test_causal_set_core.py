"""Unit tests for core causal set behavior."""

from causal_set_engine.core.causal_set import CausalSet


def test_basic_relations_and_interval() -> None:
    cset = CausalSet()
    cset.add_relation(0, 1)
    cset.add_relation(1, 2)

    assert cset.is_related(0, 2)
    assert cset.future_of(0) == {1, 2}
    assert cset.past_of(2) == {0, 1}
    assert cset.interval(0, 2) == {1}
    assert cset.cardinality() == 3


def test_cycle_rejected() -> None:
    cset = CausalSet()
    cset.add_relation(0, 1)

    try:
        cset.add_relation(1, 0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected cycle-creating relation to be rejected")


def test_transitive_validation() -> None:
    cset = CausalSet()
    cset.add_relation(0, 1)
    cset.add_relation(1, 2)

    assert cset.validate_acyclic()
    assert cset.validate_transitive()
