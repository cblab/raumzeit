"""Tests for phase-2a minimal growth sandbox validity."""

from causal_set_engine.generators.phase2_minimal_growth import generate_minimal_growth_causal_set


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
