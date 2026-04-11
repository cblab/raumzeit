"""Tests for growth-family generator validity."""

from causal_set_engine.generators.growth_family import (
    generate_age_biased_growth_causal_set,
    generate_minimal_growth_causal_set,
    generate_sparse_forward_growth_causal_set,
    generate_window_forward_growth_causal_set,
)


def test_minimal_growth_generates_valid_causal_set_for_multiple_seeds() -> None:
    for seed in range(5):
        cset = generate_minimal_growth_causal_set(
            n=30,
            link_probability=0.25,
            seed=seed,
            initial_chain_length=2,
        )
        assert cset.cardinality() == 30
        assert cset.validate_acyclic()
        assert cset.validate_transitive()


def test_minimal_growth_rejects_invalid_inputs() -> None:
    try:
        generate_minimal_growth_causal_set(n=0, link_probability=0.2, seed=1)
        assert False, "expected ValueError for n"
    except ValueError:
        pass

    try:
        generate_minimal_growth_causal_set(n=10, link_probability=1.5, seed=1)
        assert False, "expected ValueError for link_probability"
    except ValueError:
        pass

    try:
        generate_minimal_growth_causal_set(n=10, link_probability=0.2, seed=1, initial_chain_length=0)
        assert False, "expected ValueError for initial_chain_length"
    except ValueError:
        pass


def test_all_primitive_families_generate_valid_causal_sets() -> None:
    for seed in (2, 3, 4):
        sparse = generate_sparse_forward_growth_causal_set(
            n=25,
            base_link_probability=0.4,
            seed=seed,
        )
        older = generate_age_biased_growth_causal_set(
            n=25,
            link_probability=0.3,
            age_bias="older",
            seed=seed,
        )
        window = generate_window_forward_growth_causal_set(
            n=25,
            link_probability=0.3,
            lookback_window=6,
            seed=seed,
        )

        for cset in (sparse, older, window):
            assert cset.cardinality() == 25
            assert cset.validate_acyclic()
            assert cset.validate_transitive()
