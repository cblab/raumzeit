"""Unit tests for 2D Minkowski generator and relation."""

from causal_set_engine.generators.minkowski_2d import (
    Event2D,
    generate_minkowski_2d,
    minkowski_precedes,
)


def test_minkowski_precedence_lightcone_condition() -> None:
    a = Event2D(t=0.0, x=0.0)
    b = Event2D(t=2.0, x=1.0)
    c = Event2D(t=1.0, x=2.0)

    assert minkowski_precedes(a, b)
    assert not minkowski_precedes(a, c)


def test_generator_reproducibility_with_seed() -> None:
    cset1, events1 = generate_minkowski_2d(n=10, seed=42)
    cset2, events2 = generate_minkowski_2d(n=10, seed=42)

    assert events1 == events2
    assert cset1.direct_relations == cset2.direct_relations
    assert cset1.cardinality() == 10
