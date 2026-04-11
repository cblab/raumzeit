# causal-set-engine (Phase 1)

This folder contains a **minimal Python package scaffold** for phase-1 calibration of causal set tooling.

## Phase-1 goal

Build a clean, testable baseline architecture for:

- a core causal set data structure
- 2D Minkowski sprinkling generation
- a random-poset null model
- basic diagnostics
- lightweight tests
- explicit config and demo entrypoint

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

## Quickstart

From this folder:

```bash
pip install -e .
pytest -q
python -m causal_set_engine.experiments.run_phase1_demo --n 50 --seed 7
```
