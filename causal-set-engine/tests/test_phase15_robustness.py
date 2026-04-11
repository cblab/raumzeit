"""Lightweight deterministic phase-1.5 robustness checks."""

from causal_set_engine.diagnostics.basic import (
    estimate_dimension_chain_height,
    longest_chain_length,
    sampled_interval_statistics,
)
from causal_set_engine.generators.minkowski_2d import generate_minkowski_2d
from causal_set_engine.generators.minkowski_3d import generate_minkowski_3d
from causal_set_engine.generators.minkowski_4d import generate_minkowski_4d
from causal_set_engine.generators.null_models import generate_fixed_edge_count_poset
from causal_set_engine.generators.random_poset import generate_random_poset


GENS = {
    2: generate_minkowski_2d,
    3: generate_minkowski_3d,
    4: generate_minkowski_4d,
}


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _collect_metrics(dim: int, n: int, seed_start: int, runs: int) -> dict[str, list[float]]:
    gen = GENS[dim]
    minkowski_dim = []
    minkowski_chain = []
    minkowski_interval = []

    null1_dim = []
    null1_chain = []
    null1_interval = []

    null2_dim = []
    null2_chain = []
    null2_interval = []

    edge_count = int(round(0.22 * (n * (n - 1) / 2)))

    for seed in range(seed_start, seed_start + runs):
        mk_cset, _ = gen(n=n, seed=seed)
        rp_cset = generate_random_poset(n=n, relation_probability=0.22, seed=seed)
        fe_cset = generate_fixed_edge_count_poset(n=n, edge_count=edge_count, seed=seed)

        mk_interval = sampled_interval_statistics(mk_cset, pairs=30, seed=seed)
        rp_interval = sampled_interval_statistics(rp_cset, pairs=30, seed=seed)
        fe_interval = sampled_interval_statistics(fe_cset, pairs=30, seed=seed)

        minkowski_dim.append(estimate_dimension_chain_height(mk_cset))
        minkowski_chain.append(float(longest_chain_length(mk_cset)))
        minkowski_interval.append(float(mk_interval["mean"] or 0.0))

        null1_dim.append(estimate_dimension_chain_height(rp_cset))
        null1_chain.append(float(longest_chain_length(rp_cset)))
        null1_interval.append(float(rp_interval["mean"] or 0.0))

        null2_dim.append(estimate_dimension_chain_height(fe_cset))
        null2_chain.append(float(longest_chain_length(fe_cset)))
        null2_interval.append(float(fe_interval["mean"] or 0.0))

    return {
        "minkowski_dim": minkowski_dim,
        "minkowski_chain": minkowski_chain,
        "minkowski_interval": minkowski_interval,
        "null1_dim": null1_dim,
        "null1_chain": null1_chain,
        "null1_interval": null1_interval,
        "null2_dim": null2_dim,
        "null2_chain": null2_chain,
        "null2_interval": null2_interval,
    }


def test_minkowski_vs_nulls_remain_distinguishable_in_2d_3d_4d() -> None:
    for dim in (2, 3, 4):
        metrics = _collect_metrics(dim=dim, n=75, seed_start=200, runs=4)

        assert _mean(metrics["minkowski_dim"]) > _mean(metrics["null1_dim"]) + 0.3
        assert _mean(metrics["minkowski_dim"]) > _mean(metrics["null2_dim"]) + 0.3

        assert _mean(metrics["minkowski_chain"]) < _mean(metrics["null1_chain"]) - 1.0
        assert _mean(metrics["minkowski_chain"]) < _mean(metrics["null2_chain"]) - 1.0

        assert _mean(metrics["minkowski_interval"]) < _mean(metrics["null1_interval"]) - 0.5
        assert _mean(metrics["minkowski_interval"]) < _mean(metrics["null2_interval"]) - 0.5
