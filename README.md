# FP-GNN Toxicity Predictor 1.0.0 (`bsp-tox-fpgnn`)

Offline, inference-only container that predicts the probability of 631 toxicity
endpoints (Tox21 12 · ClinTox 2 · ToxCast 617) for small molecules given as
SMILES/SDF/MOL. One multi-task FP-GNN network combines a fingerprint branch
(MACCS + ErG + PubChem, 1,489 bits) with a graph-attention branch over the
atoms (Cai et al., Brief. Bioinform. 2022).

* Deployment type **T2 (batch)**: runs one job and exits, with progress logs,
  checkpoint/restart and run-time reporting. An optional HTTP mode is included.
* Runs with **no network** (`--network none`), as a **non-root** user, on
  **linux/amd64**, GPU (CUDA 11.8 runtime bundled) or CPU.
* No login or user management.

```bash
docker run --rm --gpus all --network none \
  -v "$PWD/input:/data/input:ro" -v "$PWD/output:/data/output" \
  -e INPUT_PATH=/data/input/molecules.csv \
  pzkeung/bio-synergy-platform:fp-gnn-1.0.0
# -> output/predictions.csv, output/run_summary.json
```

## Repository layout

| Path | Content |
|---|---|
| `tool.yaml` | Tool metadata: id/version, inputs, parameters, outputs, performance, seed/tolerance, T2 type, resources, limitations |
| `Dockerfile`, `requirements.in`, `constraints.txt`, `requirements.lock` | Reproducible image build (pinned base digest and apt versions; hash-locked dependencies matching the training image) |
| `docker-compose.yml` | Deployment manifest (batch job with `network_mode: none`; optional `serve` profile) |
| `src/fpgnn_tox/` | Inference package (`python -m fpgnn_tox batch|serve|openapi|version`) written for this delivery |
| `src/pybiomed/` | PubChem fingerprint code vendored unmodified from PyBioMed, with its BSD-3-Clause license |
| `api/openapi.yaml` | HTTP API specification (OpenAPI 3.0.3) for `serve` mode |
| `models/` | Weights (`.pt` not in git) + config + `SHA256SUMS` + `README.md` |
| `tests/golden/` | Golden set: N1–N3 normal, B1–B2 boundary, E1–E2 error (input/expected file pairs) |
| `tests/cases/` | Supplementary cases S1–S11 |
| `tests/run_tests.py`, `tests/make_report.py` | Self-test runner and report generator (Python stdlib + Docker only) |
| `docs/` | User manual, model card, self-test report, reference data, license confirmation, deployment, release info |

## Key numbers

| | |
|---|---|
| Training data (*trainset*) | Tox21 + ClinTox + ToxCast merged, 10,974 molecules, 631 tasks |
| Model | holdout split seed 0 (best validation AUROC of 5 seeds) |
| Test performance (seed 0 test, 506 molecules) | macro AUROC 0.713 · F1 0.272 · sensitivity 0.262 · specificity 0.875 |
| 5-seed test AUROC | 0.712 ± 0.006 |
| Reproducibility | seed 42, float64, deterministic; tolerance 1e-6 on probabilities (measured difference 0) |
| Throughput | ~66 molecules/s with a GTX 1080 Ti, 3.1/s on CPU; model load ~1 s |

See `docs/model_card.md` before interpreting results.

## License

No license file is provided for this repository: the original FP-GNN
repository (idrugLab/FP-GNN) has no license, so none is added here, and none
of its code is included. `src/pybiomed/` keeps PyBioMed's BSD-3-Clause license.
Details: `docs/license_confirmation.md`.
