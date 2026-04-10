# emergent-geometry-causal-graphs

A compact research scaffold for stochastic graph growth experiments with per-step structural diagnostics.

The current simulation slice is now runnable end-to-end:
- single-run execution from YAML config,
- deterministic batch execution over model configs and seeds,
- raw JSON result capture,
- summary statistics aggregation,
- first baseline K1 figure generation.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run a single simulation

```bash
python scripts/run_single.py --config configs/baseline.yaml
```

Save full JSON output:

```bash
python scripts/run_single.py \
  --config configs/baseline.yaml \
  --seed 123 \
  --output results/raw/baseline/seed_123.json
```

## Run a paper-style batch

```bash
python scripts/run_batch.py --config configs/paper_batch.yaml
```

This runs each listed model config for each listed seed and stores raw outputs at:

- `results/raw/{model_name}/seed_{seed}.json`
- `results/manifests/batch_manifest.json`

## Summarize results

```bash
python scripts/summarize_results.py
```

Summaries are written to:

- `results/summary/{model_name}_summary.json`

Each summary includes:
- mean final K1
- std final K1
- mean final number of nodes
- mean final active edge count
- number of runs

## Make first figure

```bash
python scripts/make_figures.py
```

This creates:

- `figures/fig1_baseline_k1.png`

based on all baseline seeds under `results/raw/baseline/`.

## Config notes

Model configs are YAML files loaded through `src/config.py`.

A config can inherit from another config using:

```yaml
inherits: baseline.yaml
```

Inheritance is deterministic and deep-merges dictionaries with child values overriding parent values.
