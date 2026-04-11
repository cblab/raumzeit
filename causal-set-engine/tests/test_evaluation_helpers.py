"""Tests for shared evaluation helper modules."""

from causal_set_engine.evaluation.metrics import DEFAULT_METRICS, pair_quality_rows, run_once
from causal_set_engine.evaluation.sampling import batch_rows, edge_count_from_density
from causal_set_engine.generators.minkowski_2d import generate_minkowski_2d
from causal_set_engine.generators.random_poset import generate_random_poset


def test_run_once_exposes_default_metric_fields() -> None:
    cset, _ = generate_minkowski_2d(n=20, seed=7)
    row = run_once(cset, interval_samples=8, seed=7)

    for metric in DEFAULT_METRICS:
        assert metric in row
    assert "interval_median" in row


def test_batch_rows_and_pair_quality_rows_shapes() -> None:
    mk_rows = {20: batch_rows(lambda n, seed: generate_minkowski_2d(n=n, seed=seed)[0], 20, 3, 10, 8)}
    null_rows = {20: batch_rows(lambda n, seed: generate_random_poset(n=n, relation_probability=0.2, seed=seed), 20, 3, 10, 8)}

    rows = pair_quality_rows(
        n_values=[20],
        mk_rows_by_n=mk_rows,
        null_rows_by_n=null_rows,
        null_model_name="random-poset",
    )
    assert len(rows) == len(DEFAULT_METRICS)


def test_edge_count_from_density_rounds_to_forward_edge_budget() -> None:
    # n=10 => max forward edges = 45
    assert edge_count_from_density(10, 0.2) == 9
