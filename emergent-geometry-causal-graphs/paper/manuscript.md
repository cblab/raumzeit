# Local Causal Edge Dynamics Fail to Stabilize Robust Macroscopic Geometry: A Canonical 3-Model Falsification Study

## Abstract
We test a narrow hypothesis: whether a specific class of local, causal, edge-based update rules on growing directed graphs can stabilize robust macroscopic geometry. The contribution is not a claim of emergent spacetime. The contribution is a maintained modular engine, a canonical three-model ablation (`baseline_ref`, `v8a_fast`, `v9a_fast`), a reproducible diagnostics stack (K1, K2, K4, K5, K7), and a disciplined negative result.

Geometry is measured rather than assumed. The workflow is fixed to config → batch → raw outputs → summary tables → figures → commit hash. Within this canonical scope, the baseline mechanism does not stabilize robust macroscopic isotropic geometry. `v8a_fast` improves local ball integrity and selected diagnostics through local contrast and weight calibration, but does not change the asymptotic geometry class. `v9a_fast` adds mesoscale ball coherence and pushes these effects further, but still does not yield robust macroscopic isotropic geometry. The mechanism line organizes transport and local patch structure, yet remains in an anisotropic diffusion-geometric patch regime.

## 1. Introduction
This paper asks one focused question: **can this specific local causal mechanism class stabilize robust macroscopic geometry, as measured from graph dynamics alone?**

The study is falsification-driven. We do not assume an ambient manifold, target metric, or pre-imposed geometric law. We evaluate whether geometry-like behavior appears and remains stable under growth. If it does not, we report the boundary of the mechanism rather than reinterpret failure as success.

Accordingly, geometry is operationalized through diagnostics: diffusion scaling, volume growth scaling, concentration/efficiency/path structure, shell/front organization, and fixed-anchor isotropy and transport splits. These observables are designed to discriminate local structural improvements from true macroscopic geometric stabilization.

## 2. Canonical scope and implementation status
The maintained operational truth is the modular engine in:

- `emergent-geometry-causal-graphs/src/`
- canonical configs in `emergent-geometry-causal-graphs/configs/`
- canonical scripts in `emergent-geometry-causal-graphs/scripts/`

The **canonical scientific scope** of this manuscript is exactly:

- `baseline_ref` (`configs/baseline_ref.yaml`)
- `v8a_fast` (`configs/v8a_fast.yaml`)
- `v9a_fast` (`configs/v9a_fast.yaml`)

Canonical batch definition:

- `configs/paper_batch_ref.yaml`

Archival monolith status:

- `archive/reference-monolith/` is provenance only and not operational truth.

Historical variants (e.g., V7/V7.1) are non-canonical and are not part of the main proof path.

## 3. Model
### 3.1 Growth process
At step $t$, the system is a growing directed weighted graph $G_t=(V_t,E_t)$ with binary node states $s_j\in\{0,1\}$. A new node is added each step (until `max_nodes`), chooses parents from existing nodes, and receives initial incoming edges.

### 3.2 Parent selection
For candidate parent $i$, the base score is

$$
S_i^{\mathrm{base}}=\exp\big(\alpha L_i + \beta C_i + \gamma N_i\big),
$$

with local density score

$$
L_i = \frac{1}{1+\lvert k_i^{\text{out}}-\rho^*(|V_t|-1)\rvert},
$$

and novelty

$$
N_i = \frac{1}{1+k_i^{\text{out}}}.
$$

Parents are selected sequentially with genealogical repulsion using ancestry-signature Jaccard overlap

$$
J(i,\ell)=\frac{|A(i)\cap A(\ell)|}{|A(i)\cup A(\ell)|},
$$

and effective score

$$
S_i = S_i^{\mathrm{base}}\prod_{\ell\in P} \max(\varepsilon_r, 1-\lambda_r J(i,\ell)).
$$

### 3.3 State relaxation
Node states relax from weighted incoming influence:

$$
\bar s_j = \frac{\sum_{(i\to j)\in E_t^{\mathrm{act}}} w_{ij}s_i}{\sum_{(i\to j)\in E_t^{\mathrm{act}}} w_{ij}},\qquad
s_j=\mathbf 1[\bar s_j\ge 1/2].
$$

### 3.4 Baseline edge-update skeleton
For active edge $e=(i\to j)$, the update can be written as

$$
\begin{aligned}
w_e(t+1)=w_e(t)
&+\Delta_e^{\mathrm{coh}}
+\Delta_e^{\mathrm{cross}}
-\nu R_e
-\Gamma_e^{\mathrm{inh}}
-\Gamma_e^{\mathrm{crowd}}
-\Gamma_e^{\mathrm{load}}
-\Gamma_e^{\mathrm{plast}}\\
&-\Gamma_e^{\mathrm{center}}
-\Gamma_e^{\mathrm{excess}}
-\mu\big(w_e-w_0\big),
\end{aligned}
$$

with deactivation when

$$
w_e(t+1) < w_{\min}^{\mathrm{eff}}(j).
$$

The effective pruning threshold is density- and calibration-aware:

$$
w_{\min}^{\mathrm{eff}}(j)
= w_{\min}\big(1+\lambda_p\,p_j\big)\times\big(1+\alpha_{\mathrm{lift}}\,\max(0,\bar w-(w_*+\epsilon_w))\big),
$$

where $p_j=\max(0,(k_j^{\mathrm{in}}-k_{\mathrm{target}})/k_{\mathrm{target}})$ and the second factor is active only when weight calibration is enabled.

### 3.5 Variant-specific terms

- **`baseline_ref`**: disables ball-integrity contrast, weight calibration, and V9 coherence terms.
- **`v8a_fast`**: enables local ball-integrity contrast and weight calibration.
- **`v9a_fast`**: inherits `v8a_fast` and additionally enables mesoscale ball-coherence.

For `v8a_fast`, the additional local ball-integrity term is

$$
\Delta_e^{\mathrm{ball}}
=
\min\!\left(
c_{\mathrm{ball}},
\max\!\left(
-c_{\mathrm{ball}},
\alpha_{\mathrm{ball}}
\left[
\omega_{\triangle}T_{ij}
+\omega_{2h}H_{ij}
+\omega_{\deg}D_j
+\omega_{\mathrm{sh}}S_{ij}
\right]
\right)
\right).
$$

where $T_{ij}$ is triangle support, $H_{ij}$ is two-hop coverage gain, $D_j$ is degree support, and $S_{ij}$ is shared-neighbor overlap.

Weight calibration in `v8a_fast` contributes centering and excess penalties:

$$
\Gamma_e^{\mathrm{center}}
\propto
\max(0,\bar w - w_*)
\max(0,w_e - w_*),
\qquad
\Gamma_e^{\mathrm{excess}}
\propto
\max(0,w_e - (w_* + \epsilon_w)).
$$

For `v9a_fast`, mesoscale ball coherence adds

$$
\Delta_e^{\mathrm{v9}}
=
\min\!\left(
c_{\mathrm{v9}},
\max\!\left(
-c_{\mathrm{v9}},
\alpha_{\mathrm{v9}}
\left[
\omega_{r2}N_{r2}
+\omega_{r3}N_{r3}
+\omega_{\mathrm{sec}}B_{\mathrm{sec}}
-\omega_{\mathrm{red}}R_{\mathrm{inner}}
+\omega_{\mathrm{front}}F_{\mathrm{thin}}N_{r3}
\right]
\right)
\right).
$$

This term combines novelty at radius 2 and 3, sector balancing, inner redundancy suppression, and thin-front support.

## 4. Diagnostics framework
We use K1, K2, K4, K5, and K7.

- **K1 (structural stabilization):** active-edge count, degree moments, weight statistics, normalized degree entropy.
- **K2 (global diffusion/volume):** return probabilities $P(\tau)$, spectral dimension estimate, volume-growth dimension estimate on sampled BFS shadow regions.
- **K4 (concentration/efficiency/path):** incoming Herfindahl concentration, cluster dominance, sampled global efficiency, sampled path length.
- **K5 (shell/front morphology):** shell entropy, front thickness, peak shell index.
- **K7 (fixed-anchor diagnostics family):** repeated measurements around fixed seeds to separate true temporal drift from region-resampling effects.

### 4.1 K2 definitions
Spectral scaling uses return probabilities across walk horizons:

$$
P(\tau)\sim \tau^{-d_s/2}.
$$

Volume-growth scaling uses BFS-ball growth:

$$
V(r)\sim r^{d_v}.
$$

### 4.2 K7 isotropy concept and naming clarification
K7 includes anchor-local isotropy defect, diffusion splits (core/mid/front), and causal-front proxies. Isotropy defect is estimated from branch-imbalance statistics around sampled centers (coefficient-of-variation style radial imbalance).

**Naming clarification:** K7 is a diagnostics family label. It is not “Version 7.” Historical `v7`/`v71` model names are separate and non-canonical for this manuscript.

## 5. Experimental design and reproducibility
This paper is bound to the modular reproducibility chain:

1. **Config layer:** `baseline_ref`, `v8a_fast`, `v9a_fast` YAMLs.
2. **Batch layer:** `configs/paper_batch_ref.yaml` over fixed seeds.
3. **Raw outputs:** `results/raw/{model}/seed_{seed}.json`.
4. **Summary tables:** `results/summary/reference_table.json` and `.csv`.
5. **Figures:** `scripts/make_reference_figures.py`.
6. **Provenance:** record `git rev-parse HEAD` with results.

Reproducibility procedure is documented in `REPRODUCIBILITY.md`.

## 6. Results
This section reports only the canonical three-model ablation logic.

### 6.1 `baseline_ref`
The baseline mechanism produces a nontrivial sparse adaptive graph, but does not stabilize robust macroscopic isotropic geometry under the K2/K7 criteria. Diffusion/volume behavior and anchor-local isotropy diagnostics do not support a stable low-dimensional isotropic asymptotic regime.

### 6.2 `v8a_fast`
Adding ball-integrity contrast plus weight calibration improves local organization and selected diagnostic behavior (especially local ball-level structure and transport regularization), but does not change the asymptotic geometry class. The mechanism remains short of robust macroscopic isotropic stabilization.

### 6.3 `v9a_fast`
Adding mesoscale ball coherence extends these local/mesoscale improvements, yet still fails to stabilize robust macroscopic isotropic geometry at the level required by the diagnostics framework.

### 6.4 Evidence policy in the present repository state
The canonical table artifacts are designated as `results/summary/reference_table.json` and `.csv`. If these artifacts are absent or incomplete in a checkout, interpretation must remain qualitative and traceable to available raw diagnostics and scripts; no quantitative claims should be fabricated.

## 7. Interpretation
The evidence supports a narrow negative conclusion: this local causal edge-dynamics line can self-organize transport and ball-like local structure but does not robustly stabilize macroscopic isotropic geometry.

A useful description is an **anisotropic diffusion-geometric patch medium**: the system forms persistent, structured, locally coherent transport patches without converging to a globally robust isotropic geometric phase.

## 8. Limitations
- The mechanism class is heuristic and local by construction.
- Simulations are finite in size, horizon, and seed count.
- Canonical scope is intentionally narrow (three models only).
- This is not a universal no-go theorem for emergence of geometry.
- Diagnostics are strong operational proxies, not metaphysical proof.

## 9. Related work
This study is positioned among discrete causal and network-based approaches to geometric emergence, including causal sets, dynamical graph models, triangulation-based approaches, and diffusion/return-probability diagnostics in discrete geometries [REF].

Our contribution is methodological and falsification-oriented within one specific local mechanism lineage, rather than a broad unification claim [REF].

## 10. Conclusion
Within the canonical modular engine and canonical three-model ablation (`baseline_ref`, `v8a_fast`, `v9a_fast`), the tested local mechanism line is **not sufficient** to stabilize robust macroscopic isotropic geometry.

What it does provide is reproducible organization of transport and local ball structure. Future progress likely requires stronger nonlocal consistency constraints, higher-order relational structure, or different parent/selection principles beyond the present local edge-update family.

## 11. Reproducibility note
Authoritative execution path:

```bash
python scripts/run_batch.py --config configs/paper_batch_ref.yaml
python scripts/summarize_results.py
python scripts/make_reference_figures.py
git rev-parse HEAD
```

Use the resulting raw outputs, canonical reference tables, figures, and commit hash as the manuscript provenance bundle.
