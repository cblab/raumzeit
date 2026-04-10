# emergent-geometry-causal-graphs

This directory is the maintained canonical engine for the repository.

## Canonical 3-model reference ablation

Canonical scope (and only canonical scope):

- `configs/baseline_ref.yaml`
- `configs/v8a_fast.yaml`
- `configs/v9a_fast.yaml`

Canonical reference batch definition:

- `configs/paper_batch_ref.yaml`

## Canonical commands

Run from this directory (`emergent-geometry-causal-graphs/`).

1) Run canonical batch:

```bash
python scripts/run_batch.py --config configs/paper_batch_ref.yaml
```

2) Build canonical summaries/tables:

```bash
python scripts/summarize_results.py
```

3) Build canonical comparison figures for the 3-model scope:

```bash
python scripts/make_reference_figures.py
```

## Canonical references in the tree

- Engine code: `src/`
- Canonical configs: `configs/`
- Reproduction scripts: `scripts/`
- Reproducibility notes: `REPRODUCIBILITY.md`

## Notebook status

- `notebooks/exploratory_analysis.ipynb` is exploratory only.
- Notebooks are not the authoritative source of semantics or canonical execution.
- Canonical truth remains `src/` + `configs/` + `scripts/`.

## Legacy note

The root-level historical monolith was moved to `../archive/reference-monolith/` and is retained only as frozen provenance material.
