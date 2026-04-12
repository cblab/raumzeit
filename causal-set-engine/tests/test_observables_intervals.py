"""Tests for CST interval primitives."""

from causal_set_engine.core.causal_set import CausalSet
from causal_set_engine.observables.cst.intervals import (
    compute_interval_abundances,
    interval_elements,
    interval_size,
    is_link,
)


def _chain_cset(length: int) -> CausalSet:
    cset = CausalSet()
    for x in range(length):
        cset.add_element(x)
    for x in range(length - 1):
        cset.add_relation(x, x + 1)
    return cset


def _diamond_cset() -> CausalSet:
    cset = CausalSet()
    for x in range(4):
        cset.add_element(x)
    cset.add_relation(0, 1)
    cset.add_relation(0, 2)
    cset.add_relation(1, 3)
    cset.add_relation(2, 3)
    return cset


def test_interval_primitives_on_chain() -> None:
    cset = _chain_cset(4)

    assert interval_elements(cset, 0, 3) == (1, 2)
    assert interval_size(cset, 0, 3) == 2

    assert is_link(cset, 0, 1)
    assert is_link(cset, 1, 2)
    assert not is_link(cset, 0, 2)


def test_interval_primitives_on_diamond() -> None:
    cset = _diamond_cset()

    assert interval_elements(cset, 0, 3) == (1, 2)
    assert interval_size(cset, 0, 3) == 2

    assert is_link(cset, 0, 1)
    assert is_link(cset, 0, 2)
    assert is_link(cset, 1, 3)
    assert is_link(cset, 2, 3)
    assert not is_link(cset, 0, 3)


def test_interval_abundances_chain_and_diamond() -> None:
    chain = _chain_cset(4)
    diamond = _diamond_cset()

    # Chain(4): comparable pairs are (0,1),(0,2),(0,3),(1,2),(1,3),(2,3)
    # interval sizes are 0,1,2,0,1,0 -> k0=3, k1=2, k2=1
    assert compute_interval_abundances(chain, k_max=2) == {0: 3, 1: 2, 2: 1}

    # Diamond: comparable pairs are 0<1,0<2,1<3,2<3,0<3
    # interval sizes are 0,0,0,0,2 -> k0=4, k1=0, k2=1
    assert compute_interval_abundances(diamond, k_max=2) == {0: 4, 1: 0, 2: 1}
