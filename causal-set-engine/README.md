# causal-set-engine (Phase 1)

This folder contains a **minimal Python package scaffold** for phase-1 calibration of causal set tooling.

## Phase-1 goal

Build a clean, testable baseline architecture for:

- a core causal set data structure
- 2D Minkowski sprinkling generation
- a random-poset null model
- basic diagnostics
- lightweight tests
- explicit config and demo entrypoints

## Non-goals (explicit)

Phase 1 intentionally does **not** include:

- custom causal-set growth dynamics
- model fitting pipelines
- plotting/visualization stacks
- performance-heavy optimizations
- higher-dimensional spacetime generators

## Why Minkowski sprinkling first?

Poisson-like sprinkling in bounded 2D Minkowski regions is a natural first calibration target because it:

1. gives a physically interpretable baseline causal relation,
2. is simple enough to inspect and test directly,
3. provides known structural behavior (comparability and chain statistics) to benchmark diagnostics before adding dynamics.

## Local development workflow

From `causal-set-engine/`:

```bash
python -m pip install -e .
```

This editable install is the intended local workflow for the current `src/` layout.
It makes package modules and command-line entrypoints available without setting `PYTHONPATH` manually.

## Run tests

```bash
pytest -q
```

## Run demos

Single-run phase-1 demo:

```bash
causal-set-demo --n 50 --seed 7 --interval-samples 30
# equivalent:
python -m causal_set_engine.experiments.run_phase1_demo --n 50 --seed 7 --interval-samples 30
python -m causal_set_engine --n 50 --seed 7 --interval-samples 30
```

Batch phase-1 comparison (Minkowski vs random-poset null):

```bash
causal-set-batch --n 80 --runs 8 --seed-start 100 --null-p 0.2 --interval-samples 50
# equivalent:
python -m causal_set_engine.experiments.run_phase1_batch --n 80 --runs 8 --seed-start 100 --null-p 0.2 --interval-samples 50
```

## Diagnostics added for phase-1 calibration

- `longest_chain_between(x, y)` for related-pair chain reconstruction.
- `sampled_interval_statistics(...)` for compact interval-size summaries over sampled related pairs.
- `estimate_dimension_chain_height(...)` as a first, approximate phase-1 discriminator.

### Dimension-estimator caveat

`estimate_dimension_chain_height` uses a simple chain-height scaling law and is intended only as a coarse discriminator (roughly “2D-like vs not-2D-like”) in this phase. It is not a precision dimension inference method.
