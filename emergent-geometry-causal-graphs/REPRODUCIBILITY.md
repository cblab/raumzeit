# Reproducibility (Canonical Reference Ablation)

All commands in this document assume your working directory is:

- `emergent-geometry-causal-graphs/`

## 1) Canonical scope

The canonical reference ablation includes exactly:

- `baseline_ref`
- `v8a_fast`
- `v9a_fast`

Mapped configs:

- `configs/baseline_ref.yaml`
- `configs/v8a_fast.yaml`
- `configs/v9a_fast.yaml`

Canonical batch config:

- `configs/paper_batch_ref.yaml`

## 2) Environment setup

Recommended Python: **3.10+** (validated on modern CPython 3.x).

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3) Canonical batch command

```bash
python scripts/run_batch.py --config configs/paper_batch_ref.yaml
```

## 4) Summary / table command

```bash
python scripts/summarize_results.py
```

## 5) Canonical figure command

```bash
python scripts/make_reference_figures.py
```

This command generates comparison plots across `baseline_ref`, `v8a_fast`, and `v9a_fast` from available raw outputs.

## 6) Commit capture for provenance

Record the exact code revision used for a run:

```bash
git rev-parse HEAD
```

Include that hash with your run notes/manifests.

## 7) Output locations

- Raw runs: `results/raw/{model}/seed_{seed}.json`
- Batch manifest: `results/manifests/batch_manifest.json`
- Per-model summaries: `results/summary/{model}_summary.json`
- Canonical reference tables:
  - `results/summary/reference_table.json`
  - `results/summary/reference_table.csv`
- Canonical comparison figures:
  - `figures/reference_k1_trajectory.png`
  - `figures/reference_k2_ds_comparison.png` (if K2 ds exists)
  - `figures/reference_k2_dv_comparison.png` (if K2 dv exists)
  - `figures/reference_k7_ds_global_comparison.png` (if K7 ds exists)
  - `figures/reference_k7_iso_defect_comparison.png` (if K7 iso exists)
  - `figures/reference_k7_g_fc_comparison.png` (if K7 g_fc exists)

If required observables are missing, figure creation is skipped with an explicit message (no fabricated values).
