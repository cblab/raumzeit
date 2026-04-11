# Causal-Set Engine Architecture Audit (Current State)

Date: 2026-04-11
Scope: `causal-set-engine` as currently implemented.

## 1) Current architecture overview

The codebase is organized around reusable engine layers plus study orchestration:

- **Core**: `core/causal_set.py` defines causal-set structure, validation, and reachability invariants.
- **Generators**: `generators/` contains Minkowski, null, and growth-family constructors that return `CausalSet`.
- **Diagnostics**: `diagnostics/` provides reusable metric-adjacent artifact proxy computations and basic diagnostics.
- **Evaluation**: `evaluation/` centralizes row-level metric extraction, sampling helpers, pairwise comparison construction, and score aggregation.
- **Policies**: `policies/policy_gate.py` defines deterministic GO/NO-GO thresholding as a pure policy layer.
- **Experiments**: `experiments/` composes generators, evaluation, diagnostics, and policy into concrete study runs.
- **Config**: `config/` defines typed config dataclasses and loader utilities for CLI/config-file parity.

## 2) What is well separated

1. **Data model boundary is clean**: `CausalSet` remains independent from experiment-specific semantics.
2. **Evaluation math is centralized**: effect-size and aggregate scoring live in `evaluation/`, not duplicated across scripts.
3. **Policy is explicit and testable**: gate thresholds are isolated in a dedicated policy module.
4. **Diagnostics are reusable**: artifact proxies are outside experiment-specific namespaces.
5. **Entry points are thin**: CLI `run_*` modules primarily parse config and call orchestration functions.

## 3) What is still entangled

1. **Terminology lag in some identifiers/tests**: some names still carry phase-era labels even when behavior is canonical.
2. **Experiment modules own interpretation labeling**: interpretation text is tightly coupled to specific scans and parameterizations.
3. **Growth-family generator module is broad**: multiple family mechanisms and catalog metadata are colocated in one file, increasing local complexity.

## 4) Engine vs research boundary assessment

- **Engine side** (`core`, `generators`, `diagnostics`, `evaluation`, `policies`, `config`) is now mostly stable and reusable.
- **Research side** (`experiments`) is clearly the place where hypotheses, scan grids, and study conclusions are assembled.
- Boundary quality is **good**: most reusable logic is below `experiments`, and study-specific interpretation remains above it.

## 5) Top architectural strengths

1. Small, auditable pure-Python implementation with explicit dataclasses and functions.
2. Deterministic policy gate interface with transparent failure reasons.
3. Shared evaluation/scoring primitives reduce drift across study flows.
4. Typed config objects improve reproducibility and CLI/config consistency.
5. Clear top-level package segmentation supports maintainability.

## 6) Top remaining architectural weaknesses

1. Legacy-era naming remains in select internal symbols and test file names.
2. Experiment orchestration modules are still somewhat long and mix data assembly with interpretation formatting.
3. No single compact architecture reference map inside the source tree beyond module layout and tests.

## 7) Concrete next recommended architecture step

Create a small `experiments/reporting.py` layer to isolate interpretation label and table/summary formatting from experiment execution paths. This keeps experiment runners focused on computation and improves testability of interpretation logic without changing scientific scope.

## 8) Structural readiness for renewed research work

**Assessment: yes.** The engine is structurally ready for renewed research work.

Reason: reusable computational layers are separated from study orchestration, canonical surfaces are clear, and remaining issues are incremental maintainability concerns rather than blocking structural debt.
