# Model weights

SSL-GCN trains one graph convolutional network per task. The submitted weight
set is the trainset holdout **seed 0** run: 601 task models.

| Path | Content |
|---|---|
| `tasks.json` | Task output order (601 tasks, trainset column order) and the 30 trainset tasks without a model |
| `tasks/<task>/model.pth` | Mean-Teacher **teacher** weights, `{"model_state_dict": ...}` (dgllife `GCNPredictor`) — 601 files, 238,364,413 bytes in total (~397 KB each) |
| `tasks/<task>/configure.json` | Hyper-parameters used to build and train that task model |
| `SHA256SUMS` | SHA-256 of all 1,202 task files and `tasks.json` |

`model.pth` files are kept as separate files (not tracked in git — see
`.gitignore`) and are copied into the container image at build time. The
container verifies every entry of `SHA256SUMS` at start-up
(`VERIFY_CHECKSUM=1`). The SHA-256 of `SHA256SUMS` itself identifies the whole
weight set and is written to `run_summary.json` as `model_sha256`:

```
SHA256SUMS  95e9a2cdd3801bf553c027d13c3a909127286be8c0dcc7d27b241101d85f352b
tasks.json  28430ea5bea514898d309cddc6714369123e27e3af681ddaf7c43696a74ebba4
```

All 601 models share one architecture (verified from every `configure.json`):
6 GraphConv layers × 64 hidden units (sum aggregation, no degree normalization),
ReLU, batch norm, dropout 0.042, no residual; weighted-sum-and-max readout
(128-dim); MLP head 128 → 512 (ReLU, batch norm) → 1; 94,018 parameters per
task model. Input: 74-dim `CanonicalAtomFeaturizer` node features on a graph
with self-loops; no bond features.

Verify manually:

```bash
cd models && sha256sum -c SHA256SUMS
```
