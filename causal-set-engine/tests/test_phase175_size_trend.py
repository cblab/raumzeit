"""Lightweight fixed-seed size trend checks for phase-1.75."""

from causal_set_engine.diagnostics.basic import (
    estimate_dimension_chain_height,
    longest_chain_length,
    sampled_interval_statistics,
)
from causal_set_engine.experiments.decision_metrics import standardized_effect_size
from causal_set_engine.generators.minkowski_2d import generate_minkowski_2d
from causal_set_engine.generators.random_poset import generate_random_poset


def _metric_values(n: int, seeds: list[int]) -> dict[str, list[float]]:
    mk_dim: list[float] = []
    mk_chain: list[float] = []
    rp_dim: list[float] = []
    rp_chain: list[float] = []
    mk_interval: list[float] = []
    rp_interval: list[float] = []

    for seed in seeds:
        mk, _ = generate_minkowski_2d(n=n, seed=seed)
        rp = generate_random_poset(n=n, relation_probability=0.22, seed=seed)

        mk_dim.append(estimate_dimension_chain_height(mk))
        rp_dim.append(estimate_dimension_chain_height(rp))
        mk_chain.append(float(longest_chain_length(mk)))
        rp_chain.append(float(longest_chain_length(rp)))
        mk_interval.append(float(sampled_interval_statistics(mk, pairs=24, seed=seed)["mean"] or 0.0))
        rp_interval.append(float(sampled_interval_statistics(rp, pairs=24, seed=seed)["mean"] or 0.0))

    return {
        "mk_dim": mk_dim,
        "rp_dim": rp_dim,
        "mk_chain": mk_chain,
        "rp_chain": rp_chain,
        "mk_interval": mk_interval,
        "rp_interval": rp_interval,
    }


def test_at_least_one_primary_diagnostic_improves_with_larger_n() -> None:
    seeds = [700, 701, 702, 703]
    small = _metric_values(n=50, seeds=seeds)
    large = _metric_values(n=90, seeds=seeds)

    dim_small = abs(standardized_effect_size(small["mk_dim"], small["rp_dim"]))
    dim_large = abs(standardized_effect_size(large["mk_dim"], large["rp_dim"]))

    chain_small = abs(standardized_effect_size(small["mk_chain"], small["rp_chain"]))
    chain_large = abs(standardized_effect_size(large["mk_chain"], large["rp_chain"]))

    interval_small = abs(standardized_effect_size(small["mk_interval"], small["rp_interval"]))
    interval_large = abs(standardized_effect_size(large["mk_interval"], large["rp_interval"]))

    assert any(
        later >= earlier
        for earlier, later in (
            (dim_small, dim_large),
            (chain_small, chain_large),
            (interval_small, interval_large),
        )
    )
