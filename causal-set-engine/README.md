# causal-set-engine

`causal-set-engine` provides a compact, function-centric causal-set calibration engine with a clear boundary between reusable engine layers and study orchestration.

## Current architecture

```text
src/causal_set_engine/
  core/           # causal-set structure and invariants
  generators/     # Minkowski, null, and growth-family constructors
  diagnostics/    # reusable diagnostics and artifact proxy computations
  observables/    # CST-specific research observables layered above diagnostics
  evaluation/     # metrics, sampling helpers, and scoring math
  policies/       # explicit GO/NO-GO decision policy
  experiments/    # study orchestration built on engine APIs
  config/         # typed run configs and config-file loaders
  visualization/  # lightweight static plotting helpers for workflow outputs
```

## Canonical researcher CLI

The canonical researcher-facing interface is a single root command with workflow subcommands:

```bash
causal-set run --n 50 --seed 7 --interval-samples 30
causal-set run --config configs/diagnostic_demo.yaml

causal-set calibrate --dimension 3 --n-values 60,80,100 --runs 8 --seed-start 100 --null-p 0.2 --null-edge-density 0.2 --interval-samples 50

causal-set evaluate-growth --n-values 60,80 --runs 8 --seed-start 100 --growth-link-probability 0.2

causal-set scan-artifacts --n-values 60,80 --runs 8 --seed-start 100 --link-density-grid 0.16,0.22,0.28 --bias-strength-grid 0.0,0.5,1.0

causal-set evaluate-myrheim --dimensions 2,3,4 --n-values 40,80,120 --runs 8 --seed-start 100 --null-p 0.2 --null-edge-density 0.2

causal-set evaluate-intervals --dimensions 2,3,4 --n-values 40,80,120 --runs 8 --seed-start 100 --k-max 5 --null-p 0.2 --null-edge-density 0.2

causal-set evaluate-midpoint --dimensions 2,3,4 --n-values 40,80,120 --runs 8 --seed-start 100 --min-interval-size 8 --max-sampled-intervals 64 --null-p 0.2 --null-edge-density 0.2

causal-set evaluate-layers --dimensions 2,3,4 --n-values 40,80,120 --runs 8 --seed-start 100 --min-interval-size 8 --max-sampled-intervals 64 --null-p 0.2 --null-edge-density 0.2
```

This is the preferred interface for researchers on Linux, macOS, and Windows.

### Cross-platform module fallbacks

If the console script is not available in your shell, use Python module invocation:

```bash
python -m causal_set_engine.cli run --n 50 --seed 7
python -m causal_set_engine.cli calibrate --n-values 60,80 --runs 8
python -m causal_set_engine.cli evaluate-growth --n-values 60,80 --runs 8
python -m causal_set_engine.cli scan-artifacts --n-values 60,80 --runs 8
python -m causal_set_engine.cli evaluate-myrheim --dimensions 2,3,4 --n-values 40,80 --runs 8
python -m causal_set_engine.cli evaluate-intervals --dimensions 2,3,4 --n-values 40,80 --runs 8 --k-max 5
python -m causal_set_engine.cli evaluate-midpoint --dimensions 2,3,4 --n-values 40,80 --runs 8 --min-interval-size 8 --max-sampled-intervals 64
python -m causal_set_engine.cli evaluate-layers --dimensions 2,3,4 --n-values 40,80 --runs 8 --min-interval-size 8 --max-sampled-intervals 64
```

An additional package-level fallback is also supported:

```bash
python -m causal_set_engine run --n 50 --seed 7
```

Legacy separate workflow modules remain available internally for compatibility, but the canonical researcher workflow is `causal-set <subcommand> ...`.


## Research visualization layer (lightweight, static)

`causal_set_engine.visualization` adds a small plotting layer for researcher-facing inspection of workflow outputs.

Design constraints:
- static files only (`matplotlib`, headless-safe Agg backend),
- no GUI/dashboard/web app,
- no reimplementation of scientific metrics in plotting modules,
- plotting remains subordinate to `observables/` + `evaluation/` outputs.

### Available plotting modules

- `visualization/trends.py`
  - Myrheim-Meyer summary trend plots over `N`
  - midpoint-derived dimension trend plots over `N`
  - layer-profile occupied-layer summary trends over `N`
- `visualization/distributions.py`
  - interval-abundance grouped bars by `k` for each `N`
  - supports side-by-side model comparison across Minkowski references and null baselines
  - can write both count and density views
- `visualization/profiles.py`
  - individual sampled interval layer-profile plots (`layer index -> element count`)
  - compact boundary-fraction summary trend plot

### Workflow integration

Plotting is opt-in via conservative workflow flags:

```bash
causal-set evaluate-myrheim --plot --output-dir artifacts/plots/evaluate-myrheim
causal-set evaluate-midpoint --plot --output-dir artifacts/plots/evaluate-midpoint
causal-set evaluate-intervals --plot --output-dir artifacts/plots/evaluate-intervals
causal-set evaluate-layers --plot --output-dir artifacts/plots/evaluate-layers --max-profile-plots 12
```

The same flags work with module invocation on Linux/macOS/Windows:

```bash
python -m causal_set_engine.cli evaluate-layers --plot --output-dir artifacts/plots/evaluate-layers
```

Headless note: the plotting helpers force the `Agg` backend, so figure generation works in non-GUI environments (CI, remote shells, WSL, containers).

### Interpretation guidance and current pressure points

Plots are for debugging, exploration, and communication. They are **not** primary scientific evidence by themselves.

Current data-shape pressure points exposed by plotting:
- layer profiles often have unequal heights, so direct cross-interval shape comparison is limited,
- richer workflow result dataclasses may eventually help plotting ergonomics,
- profile normalization/aggregation is intentionally deferred and may belong to future evaluation-layer work.

## Functional boundaries

- Engine modules (`core`, `generators`, `diagnostics`, `evaluation`, `policies`, `config`) are reusable and function-centric.
- CST-standard observables live in `observables/cst/` so theory-specific estimators stay distinct from generic engine diagnostics.
- `experiments` modules assemble concrete study flows, invoke policy decisions, and return auditable result structures.
- Policy thresholds are explicit in `policies/policy_gate.py`; scoring and metric math are centralized in `evaluation/`.

## Myrheim-Meyer dimension estimator

`causal_set_engine.observables.cst.myrheim_meyer` adds a transparent Myrheim-Meyer dimension estimator based on ordering fraction:

- ordering fraction: `r = R / (N (N-1))`, where `R` is the number of ordered comparable pairs `x ≺ y`,
- continuum model used for inversion:
  `C(d) = Gamma(d + 1) * Gamma(d / 2) / (4 * Gamma(3 d / 2))`,
- estimator: deterministic bisection solve of `C(d) = r` on a fixed bracket.

This differs from `diagnostics.basic.estimate_dimension_chain_height`, which is a coarse chain-growth scaling proxy (`log N / log L`) used for lightweight calibration. Myrheim-Meyer is a CST-standard observable tied directly to pair-ordering statistics, but still remains a finite-size/region-sensitive estimator.

### Limitations

- The estimator is calibrated to Alexandrov-interval-style Minkowski sprinklings; non-interval regions can shift recovered dimensions.
- Small `N` can produce high variance.
- Returned values are clipped to the configured bracket when ordering fractions fall outside model range.

## Alexandrov interval toolkit (global CST observables)

`causal_set_engine.observables.cst.intervals` adds the first reusable interval-structure toolkit for global CST analysis:

- **Alexandrov interval**: for comparable elements `x ≺ y`, `I(x, y) = {z | x ≺ z ≺ y}`.
- **Links**: comparable pairs with empty strict intervals (`|I(x, y)| = 0`), reported as the `k=0` / `N0` interval-abundance bin.
- **Interval abundances**: histogram counts/densities of `|I(x, y)| = k` over ordered comparable pairs.

Why this matters:

- Global interval abundances are a foundational CST structure signal and an auditable baseline against null models.
- This layer is intentionally conservative: it provides reusable interval primitives and global statistics only.
- It is a prerequisite toolkit for later action-based observables (including BD-action studies), which are intentionally out of scope here.

### Focused global interval workflow

Use the new researcher entrypoint to compare Minkowski references against null baselines:

```bash
causal-set evaluate-intervals --dimensions 2,3,4 --n-values 40,80,120 --runs 8 --k-max 5
```

The workflow reports per-model/per-`N` interval abundance counts and densities by `k`, explicitly highlights `k=0` links, and keeps interpretation restricted to global interval statistics.


## Midpoint-scaling observable

`causal_set_engine.observables.cst.midpoint_scaling` adds interval-based midpoint scaling as an explicit CST geometric sensor built directly on the interval toolkit.

- **Midpoint candidate selection**: for each comparable pair `x ≺ y`, choose `z in I(x,y)` minimizing sub-interval asymmetry `||I(x,z)|-|I(z,y)||`, with deterministic tie-breaking.
- **Primary statistic**: `S = N_xy / ((N_xz + N_zy)/2)` with inclusive counts `N_ab = |I(a,b)| + 2`.
- **Derived estimate (secondary)**: `d_hat = log2(S)` as a convenience estimate, reported separately from `S`.

Why sampled qualifying intervals (not one privileged interval):

- finite causal sets contain many valid intervals with varying sizes and noise levels,
- restricting to one hand-picked interval can hide variance and introduce accidental bias,
- deterministic sampled qualifying intervals provide reproducible coverage while keeping runtime bounded.

How this differs from Myrheim-Meyer:

- Myrheim-Meyer is a **global pair-ordering** observable driven by ordering fraction over the whole set,
- midpoint scaling is an **interval-localized split** observable that aggregates many sampled intervals and tests sub-interval balance/scaling behavior.

Limitations:

- small intervals are noisy and can be under-sampled when strict size thresholds are high,
- midpoint-derived dimension estimates are finite-size diagnostics for calibration, not standalone theory claims,
- this workflow does **not** add local curvature interpretation and does **not** include BD-action logic.

### Focused midpoint workflow

```bash
causal-set evaluate-midpoint --dimensions 2,3,4 --n-values 40,80,120 --runs 8 --min-interval-size 8 --max-sampled-intervals 64
```

The workflow reports compact answers on: dimensional discrimination (2D/3D/4D), separation from current null baselines, comparison versus Myrheim-Meyer and chain-height proxy, and where results are under-sampled.


## Interval layer-profile observable

`causal_set_engine.observables.cst.layer_profiles` adds a structural interval-internal profile:

- for one comparable pair `x ≺ y`, use strict interval elements `I(x, y)` only (endpoints excluded),
- assign each internal element `z` to layer index `L(z)` by internal predecessor depth from `x`:
  - `L(z)=0` if no internal predecessor `w` satisfies `x ≺ w ≺ z`,
  - else `L(z)=1+max(L(w))` over internal predecessors,
- the profile is a count tuple by occupied layer index, starting at layer `0`.

Summary helpers expose compact shape descriptors (occupied layer count, peak layer size/index, and boundary mass fraction).

How this differs from midpoint scaling and Myrheim-Meyer:

- Myrheim-Meyer is global pair-ordering structure over whole sets,
- midpoint scaling is interval split-scaling around selected midpoints,
- layer profiles are interval-internal depth-distribution shapes across sampled intervals.

Limitations:

- small strict intervals can be noisy and frequently under-sampled,
- profile comparison across intervals with very different heights can be unstable,
- this workflow is structural only: no curvature claims, no action-based logic.

### Focused layer-profile workflow

```bash
causal-set evaluate-layers --dimensions 2,3,4 --n-values 40,80,120 --runs 8 --seed-start 100 --min-interval-size 8 --max-sampled-intervals 64
```

The workflow reports conservative separation summaries versus current null baselines and compares effect-size strength against midpoint scaling and Myrheim-Meyer without imposing directional dimension assumptions.
