# Causal-Set Engine Architecture Audit & Refactor Plan

Date: 2026-04-11
Scope: current `causal-set-engine` package, with phase-2 dynamics work treated as requirements discovery.

## Refactor status snapshot (updated after Stage 7 implementation)

- ✅ Stage 1 complete: shared evaluation helpers (`evaluation.metrics`, `evaluation.sampling`) are in place and used.
- ✅ Stage 2 complete: decision/scoring math lives in `evaluation.scoring` with compatibility shims.
- ✅ Stage 3 complete: artifact proxies are in `diagnostics.artifact_proxies` with compatibility re-export.
- ✅ Stage 4 complete: phase-2 gate policy is in `policies.phase2_gate` with compatibility path retained.
- ✅ Stage 5 complete: experiment modules are orchestration-focused with reduced cross-experiment coupling.
- ✅ Stage 6 complete: typed run config dataclasses and lightweight loaders added under `config/`; CLI defaults preserved with optional `--config` support.
- ✅ Stage 7 complete: README/AGENTS/plan documentation aligned to current architecture and boundaries.

### Remaining open work

- No additional refactor stage is currently open in this plan.
- **Next required step:** run a fresh post-Stage-7 architecture audit and publish a new audit document; keep this file as the active historical plan reference until that new audit is complete.

## A) Concise architecture audit

### What is already well separated

1. **Core data structure is small and generic.**
   `core/causal_set.py` defines a compact, dependency-free `CausalSet` with validation and reachability operations and no model-specific physics assumptions.

2. **Generators are mostly isolated from diagnostics.**
   Minkowski, random-poset, and phase-2 growth generators are in `generators/` and return `CausalSet` instances without embedding analysis logic.

3. **Phase-2 policy is explicit and auditable.**
   The gate in `experiments/phase2_policy.py` is threshold-driven and easy to reason about.

4. **Decision math is centralized.**
   Effect sizes, overlap, trend checks, and aggregate scoring are grouped in `experiments/decision_metrics.py`.

5. **CLI entrypoints are thin wrappers.**
   `run_phase*` scripts mostly orchestrate calls instead of encoding large frameworks.

### What is entangled

1. **Engine-level metric extraction is duplicated in experiment modules.**
   `_run_once`, `_batch_rows`, `_pair_quality_rows`, and edge-density helpers are redefined and reused across `run_phase1_batch.py`, `phase2a_probe.py`, and `phase2c_scan.py`.

2. **Research policy and general evaluation machinery are co-located.**
   Reusable evaluation primitives (metric rows, batch loops) live in `experiments/` beside phase-specific go/no-go policy and naming.

3. **Artifact proxies are placed under experiments though they are reusable diagnostics.**
   `experiments/artifact_proxies.py` currently acts like a diagnostics submodule.

4. **Family-specific assumptions leak into shared flow.**
   `phase2c_scan.py` imports internal helpers from `phase2a_probe.py` and is tightly coupled to the age-biased family and the fixed metric tuple.

5. **Naming and package boundaries center “phase” workflows rather than engine primitives.**
   The package structure privileges chronological study phases over stable architectural seams.

### What should move where

- Move reusable metric extraction / batch orchestration into an engine-level evaluation module (new `evaluation/`).
- Move artifact proxies into `diagnostics/`.
- Keep phase gates, scan grids, and interpretation labels in `experiments/`.
- Keep generator family catalogs in `generators/` but expose a narrow registry interface for experiments.
- Move config parsing/validation into `configs/` module (Python package), keep YAML files in repository `configs/` directory.

---

## B) Target module design

## Recommended package/module structure

```text
causal_set_engine/
  core/
    causal_set.py                 # existing
    protocols.py                  # NEW: core protocol/type aliases only

  generators/
    minkowski_2d.py               # existing
    minkowski_3d.py               # existing
    minkowski_4d.py               # existing
    random_poset.py               # existing
    null_models.py                # existing
    phase2_minimal_growth.py      # existing (keep families; mark as research generator set)
    registry.py                   # NEW: name -> callable, metadata

  diagnostics/
    basic.py                      # existing core diagnostics
    artifact_proxies.py           # MOVED from experiments
    registry.py                   # NEW: metric name -> callable

  evaluation/
    metrics.py                    # NEW: MetricRow schema + metric extraction pipeline
    sampling.py                   # NEW: batch run helper(s), seed sweeps
    comparison.py                 # NEW: pairwise model comparison scaffolding
    scoring.py                    # NEW: move/generalize decision_metrics math here

  policies/
    phase2_gate.py                # MOVED from experiments/phase2_policy.py (name kept stable via shim)

  experiments/
    phase1_batch.py               # refactored orchestration only
    phase2a_probe.py              # refactored orchestration only
    phase2c_scan.py               # refactored orchestration only
    reporting.py                  # NEW: table/console formatting helpers

  config/
    schema.py                     # NEW: dataclasses for run config
    loaders.py                    # NEW: yaml -> config dataclass

  __main__.py
```

## Recommended interfaces/protocols

1. **Generator protocol (minimal):**
   - `GeneratorFn = Callable[[int, int], CausalSet]` (n, seed).
   - Optional metadata wrapper for family name + parameter labels.

2. **Diagnostic metric protocol:**
   - `MetricFn = Callable[[CausalSet, int, int], float]` or a context-based callable.
   - Registry keyed by stable metric names (`dimension_estimate`, `relation_density`, ...).

3. **Evaluation run spec:**
   - Dataclass containing `n_values`, `runs`, `seed_start`, `interval_samples`, and selected metrics.

4. **Comparison result schema:**
   - Reuse existing `PairQuality`/`DiagnosticQuality` dataclasses (moved to evaluation namespace).

5. **Policy interface:**
   - `DecisionPolicy[InputT, OutputT]` protocol with a single pure `evaluate(...)` method.

## What should be abstracted

- Repeated batch/sweep execution loops.
- Metric extraction pipeline and metric registry.
- Pairwise comparison calculations and aggregation.
- Generator family registration (name, parameters, callable).

## What should remain concrete

- Current Minkowski / null / minimal-growth generator implementations.
- Current phase-2 threshold values and decision semantics.
- Current metric formulas and artifact proxy formulas.
- CLI commands and output structure (for backward compatibility).

---

## C) Staged refactor plan (low risk, behavior-preserving)

1. **Stage 1: Consolidate duplicated evaluation helpers (highest leverage).**
   - Add `evaluation/metrics.py` with `MetricRow`, `DEFAULT_METRICS`, `run_once`.
   - Add `evaluation/sampling.py` with `batch_rows`, `edge_count_from_density`.
   - Update `run_phase1_batch.py`, `phase2a_probe.py`, `phase2c_scan.py` to import these helpers.
   - Keep old helper names as temporary wrappers for one release to reduce churn.

2. **Stage 2: Move decision math to engine-level evaluation namespace.**
   - Relocate `experiments/decision_metrics.py` -> `evaluation/scoring.py`.
   - Leave compatibility import shims in `experiments/decision_metrics.py`.
   - Verify all tests still pass unchanged.

3. **Stage 3: Move artifact proxies into diagnostics.**
   - Relocate `experiments/artifact_proxies.py` -> `diagnostics/artifact_proxies.py`.
   - Add compatibility re-export module in old path.

4. **Stage 4: Introduce explicit policy package.**
   - Move `experiments/phase2_policy.py` -> `policies/phase2_gate.py`.
   - Keep legacy import shim.

5. **Stage 5: Isolate experiment orchestration from shared engine layers.**
   - Ensure experiment modules only do assembly: choose generators, call evaluation/scoring, format results.
   - Remove cross-experiment internal imports (e.g., `phase2c_scan` importing private helpers from `phase2a_probe`).

6. **Stage 6: Add config dataclasses and loader.** ✅ complete
   - Keep existing CLI args; optionally allow `--config` parity path.
   - Map YAML to typed config for reproducibility and stable defaults.

7. **Stage 7: Documentation hardening.** ✅ complete
   - Add architecture map to README and “research vs engine” boundary table.
   - Explicitly mark phase modules as reference studies built on engine APIs.

### Non-goals during refactor

- No new dynamics families.
- No scientific-claim expansion.
- No performance rewrite.
- No dependency-heavy framework adoption.

### Overengineering risks to avoid

- Premature plugin systems with dynamic imports.
- Deep class hierarchies where plain functions + dataclasses suffice.
- Excessive generic typing that obscures domain intent.
- Splitting files too early before duplicated logic is actually removed.

---

## D) “Research vs engine” boundary document

## Engine core

Belongs here if it is:
- required by multiple studies,
- dynamics-family agnostic,
- deterministic/pure or near-pure utility logic.

Includes:
- `CausalSet` structure and invariants,
- generic diagnostics and artifact proxy computations,
- generic metric extraction and comparison math,
- generic sampling/sweep execution helpers,
- stable interfaces for generators and policies.

## Generators

Belongs here if it defines:
- a concrete causal-set construction process,
- parameterized mechanisms producing `CausalSet` instances,
- metadata useful for auditability.

Includes:
- Minkowski sprinklings,
- null baselines,
- current minimal primitive growth families.

## Experiments only

Belongs here if it is:
- phase-specific,
- tied to one hypothesis or decision gate,
- reporting/interpretation logic not universally reusable.

Includes:
- phase-2 GO/NO-GO study assembly,
- age-biased scan grids and interpretation labels,
- study-specific textual conclusions and tables.

---

## Top 5 architectural problems

1. Duplicated evaluation helper logic across experiment modules.
2. Cross-imports of private helpers between experiment modules.
3. Reusable artifact diagnostics living in experiments namespace.
4. Decision/scoring utilities named and placed as phase-specific despite broad reuse.
5. Architectural center of gravity is “phase scripts” instead of reusable engine seams.

## Top 5 architectural strengths

1. Core `CausalSet` is compact, explicit, and model-agnostic.
2. Generator implementations are readable and auditable.
3. Diagnostics are transparent, pure-Python, and test-driven.
4. Phase-2 gate is explicit and deterministic.
5. Existing codebase is small enough for incremental refactor without disruption.

## Highest-leverage next single refactor step

**Implement Stage 1 now: create a shared `evaluation` helper layer (`run_once`, `batch_rows`, `edge_count_from_density`, metric schema) and switch all current experiment modules to use it.**

Why this first:
- removes immediate duplication,
- reduces future merge conflicts,
- creates a stable seam for subsequent module moves,
- preserves behavior with minimal API surface change.
