"""Tests for higher-dimensional Minkowski generators."""

from causal_set_engine.generators.minkowski_3d import (
    Event3D,
    generate_minkowski_3d,
    minkowski_precedes as precedes_3d,
)
from causal_set_engine.generators.minkowski_4d import (
    Event4D,
    generate_minkowski_4d,
    minkowski_precedes as precedes_4d,
)


def test_minkowski_3d_precedence_lightcone_condition() -> None:
    a = Event3D(t=0.0, x=0.0, y=0.0)
    b = Event3D(t=2.0, x=1.0, y=1.0)
    c = Event3D(t=1.0, x=1.0, y=1.0)

    assert precedes_3d(a, b)
    assert not precedes_3d(a, c)


def test_minkowski_4d_precedence_lightcone_condition() -> None:
    a = Event4D(t=0.0, x=0.0, y=0.0, z=0.0)
    b = Event4D(t=3.0, x=1.0, y=1.0, z=1.0)
    c = Event4D(t=1.0, x=1.0, y=1.0, z=1.0)

    assert precedes_4d(a, b)
    assert not precedes_4d(a, c)


def test_higher_dim_generators_reproducible_and_return_coordinates() -> None:
    cset3_a, events3_a = generate_minkowski_3d(n=12, seed=11)
    cset3_b, events3_b = generate_minkowski_3d(n=12, seed=11)
    cset4_a, events4_a = generate_minkowski_4d(n=9, seed=15)
    cset4_b, events4_b = generate_minkowski_4d(n=9, seed=15)

    assert events3_a == events3_b
    assert cset3_a.direct_relations == cset3_b.direct_relations
    assert cset3_a.cardinality() == 12

    assert events4_a == events4_b
    assert cset4_a.direct_relations == cset4_b.direct_relations
    assert cset4_a.cardinality() == 9
