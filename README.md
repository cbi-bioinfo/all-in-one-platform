# SSL-GCN Toxicity Predictor 1.0.0 (`bsp-tox-sslgcn`)

Offline, inference-only container that predicts the probability of 601 toxicity
endpoints (Tox21 12 · ClinTox 2 · ToxCast 587) for small molecules given as
SMILES/SDF/MOL. Each endpoint has its own graph convolutional network
(dgllife `GCNPredictor`) trained with Mean-Teacher semi-supervised learning
(SSL-GCN, Chen et al., J. Cheminform. 2021).

* Deployment type **T2 (batch)**: runs one job and exits, with progress logs,
  checkpoint/restart and run-time reporting. An optional HTTP mode is included.
* Runs with **no network** (`--network none`), as a **non-root** user, on
  **linux/amd64**, GPU (CUDA 11.8 runtime bundled) or CPU.
* No login or user management.

```bash
docker run --rm --gpus all --network none \
  -v "$PWD/input:/data/input:ro" -v "$PWD/output:/data/output" \
  -e INPUT_PATH=/data/input/molecules.csv \
  pzkeung/bio-synergy-platform:ssl-gcn-1.0.0
# -> output/predictions.csv, output/run_summary.json
```

## Repository layout

| Path | Content |
|---|---|
| `tool.yaml` | Tool metadata: id/version, inputs, parameters, outputs, performance, seed/tolerance, T2 type, resources, limitations |
| `Dockerfile`, `requirements.in`, `constraints.txt`, `requirements.lock` | Reproducible image build (pinned base digest and apt versions, hash-locked dependencies matching the training image) |
| `docker-compose.yml` | Deployment manifest (batch job with `network_mode: none`; optional `serve` profile) |
| `src/sslgcn_tox/` | Inference package (`python -m sslgcn_tox batch|serve|openapi|version`) |
| `api/openapi.yaml` | HTTP API specification (OpenAPI 3.0.3) for `serve` mode |
| `models/` | 601 task models (`tasks/<task>/model.pth` not in git) + `configure.json` + `tasks.json` + `SHA256SUMS` + `README.md` |
| `tests/golden/` | Golden set: N1–N3 normal, B1–B2 boundary, E1–E2 error (input/expected file pairs) |
| `tests/cases/` | Supplementary cases S1–S9 (limits, format errors, checkpoint restart, standardization, RDKit-version boundary) |
| `tests/run_tests.py`, `tests/make_report.py` | Self-test runner and report generator (Python stdlib + Docker only) |
| `docs/user_manual.md` | How to run, input formats, environment variables, output interpretation, error codes |
| `docs/model_card.md` | Training data, procedure, performance, limitations |
| `docs/selftest_report.md` | Self-test results |
| `docs/reference_data.md` | Reference/training data: type, size, source, license |
| `docs/license_confirmation.md` | License review of code, weights, dependencies, data |
| `docs/deployment.md` | Build, registry, offline installation and run procedure |
| `docs/release_info.md` | Submission commit hash, image ID/digest |

## Key numbers

| | |
|---|---|
| Training data (*trainset*) | Tox21 + ClinTox + ToxCast merged, 10,974 molecules, 631 tasks (601 with a model) |
| Model | holdout split seed 0 (best validation AUROC of 5 seeds; also best on test) |
| Test performance (seed 0 test, 506 molecules) | macro AUROC 0.599 · F1 0.154 · sensitivity 0.265 · specificity 0.754 |
| 5-seed test AUROC | 0.583 ± 0.012 |
| Reproducibility | seed 42, float64, deterministic; tolerance 1e-6 on probabilities (measured difference 0) |
| Throughput | ~50 molecules/s on RTX 2080 Ti, model load ~60 s |

Predictions are over-confident (a quarter of test probabilities are exactly 0 or 1)
and the 0.5 labels miss most Tox21/ClinTox positives — use the probabilities for
ranking. See `docs/model_card.md` before interpreting results.

## License

Apache-2.0 (`LICENSE`). The original SSL-GCN repository has no license file; no
code from it is included. Third-party components: `docs/license_confirmation.md`.
