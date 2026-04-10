# raumzeit

## Canonical implementation and scope

The maintained operational engine is the **modular implementation** in:

- `emergent-geometry-causal-graphs/`

The canonical scientific reference scope is restricted to exactly three models:

- `configs/baseline_ref.yaml`
- `configs/v8a_fast.yaml`
- `configs/v9a_fast.yaml`

The canonical batch definition for this scope is:

- `configs/paper_batch_ref.yaml`

## Canonical reproduction path

From `emergent-geometry-causal-graphs/`:

```bash
python scripts/run_batch.py --config configs/paper_batch_ref.yaml
python scripts/summarize_results.py
python scripts/make_reference_figures.py
```

Detailed reproducibility instructions are in:

- `emergent-geometry-causal-graphs/REPRODUCIBILITY.md`

## Archival material (non-operational)

The historical monolith is preserved only for provenance/traceability under:

- `archive/reference-monolith/`

Root-level notebook/bootstrap leftovers are archived under:

- `archive/legacy-root/`

These archival files are **not** the maintained execution path.
