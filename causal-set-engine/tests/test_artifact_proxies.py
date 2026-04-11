from causal_set_engine.core.causal_set import CausalSet
from causal_set_engine.experiments.artifact_proxies import (
    age_layering_stratification_proxy,
    birth_order_dominance_proxy,
)


def test_birth_order_dominance_proxy_detects_early_source_dominance() -> None:
    cset = CausalSet()
    for i in range(6):
        cset.add_element(i)

    for j in range(1, 6):
        cset.add_relation(0, j)

    proxy = birth_order_dominance_proxy(cset)
    assert 0.6 <= proxy <= 1.0


def test_age_layering_proxy_detects_single_channel_stratification() -> None:
    cset = CausalSet()
    for i in range(8):
        cset.add_element(i)

    # Force all direct edges through one layer channel: old layer -> young layer.
    for src in (0, 1):
        for dst in (6, 7):
            cset.add_relation(src, dst)

    proxy = age_layering_stratification_proxy(cset, layer_count=4)
    assert proxy == 1.0
