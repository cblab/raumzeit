# Causal-Set Engine Architecture Audit (Current State)

Date: 2026-04-11  
Scope: `causal-set-engine` as currently implemented.

## Current architecture overview

The package is organized as a function-centric engine with a clear split between reusable computation layers and experiment orchestration.

- `core/`: causal-set data model, closure, reachability, and validation invariants.
- `generators/`: Minkowski constructors, null models, and growth-family constructors returning `CausalSet` objects.
- `diagnostics/`: reusable observable extraction and artifact-proxy helpers.
- `evaluation/`: scoring math, effect-size computations, sampling helpers, and aggregate ranking utilities.
- `policies/`: deterministic GO/NO-GO policy logic based on explicit thresholds.
- `config/`: typed config schemas plus CLI/config-file loading and merge behavior.
- `experiments/`: study-level orchestration that composes engine functions into specific evaluation flows.

## What is well separated

1. **Core invariants are isolated** in the data model layer and do not depend on study semantics.
2. **Metric and scoring math are centralized** in `evaluation/`, reducing duplicated ad hoc calculations.
3. **Decision policy logic is isolated** in `policies/`, making thresholds explicit and testable.
4. **Experiment runners are composition layers** that call reusable engine functions instead of embedding primitive math.
5. **Typed config loading is shared** across CLI entry points for reproducible run settings.

## What is still entangled

1. Some experiment modules still mix **numeric execution and interpretation labeling** in the same functions.
2. Growth-family orchestration paths include dense parameter handling that could be split into smaller helper units.
3. A few internal symbol names still reflect legacy naming even where behavior is already canonical.

## Engine vs research boundary

- **Engine boundary**: `core`, `generators`, `diagnostics`, `evaluation`, `policies`, and `config` form the reusable computational substrate.
- **Research boundary**: `experiments` packages specific study scenarios, scan grids, and interpretation framing on top of engine APIs.
- **Assessment**: boundary quality is solid; reusable mechanics are below `experiments`, and study framing stays above that line.

## Top strengths

1. Explicit, auditable function-based architecture with deterministic defaults.
2. Clean separation between reusable computations and scenario orchestration.
3. Test coverage across core invariants, diagnostics, generators, scoring utilities, policies, and experiment outputs.
4. Canonical CLI/config entry points that map to typed configuration objects.
5. Lightweight implementation that is easy to inspect and extend without heavy framework coupling.

## Top weaknesses

1. Experiment modules can still be long and combine orchestration with report-label formatting.
2. Some canonical surfaces depend on broad modules that could be further decomposed for maintainability.
3. Internal naming cleanup is mostly complete but not fully uniform across every non-user-facing symbol.

## Next recommended architecture step

Extract experiment result labeling/report formatting into a small dedicated helper module (for example, an `experiments/reporting.py` utility layer) so experiment evaluators focus on computation and return normalized result payloads before presentation labeling.

## Readiness for research work

**Assessment: ready.**

The codebase is structurally ready for new research runs: engine primitives are reusable, policy and scoring are explicit, and remaining issues are incremental maintainability improvements rather than blocking architecture debt.
