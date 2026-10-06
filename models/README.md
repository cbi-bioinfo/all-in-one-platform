# Model weights

One multi-task Chemprop (D-MPNN) model scores all 631 trainset tasks. The
submitted weights are the trainset holdout **seed 0** run (best validation macro
AUROC of 5 seeds, also best on the untouched test split).

| File | Size (bytes) | SHA-256 | Content |
|---|---:|---|---|
| `chemprop_trainset_seed0.pt` | 2,061,832 | `198d8179c7196618c6bcdabffb844760351ec59b880e4a2036faef46879ea462` | chemprop 2.3.1 model checkpoint (`best.pt` written by `chemprop train`): `MPNN` with 507,931 parameters, loaded with `chemprop.models.utils.load_model` |
| `chemprop_trainset_seed0_config.json` | 17,410 | `82a479b6a8c9c2f00a1e8c70c23128305f8e9e04bc7c302de162d43b38de3560` | Training settings (`task_type` classification, `hidden_size` 300, `depth` 3, `ffn_hidden_size` 300, `ffn_num_layers` 1, `dropout` 0, `epochs` 50, `lr` 0.001, `batch_size` 64, `seed` 42) and `tasks` (631 names in output order) |
| `SHA256SUMS` | — | — | Checksums of the two files above; verified at container start-up (`VERIFY_CHECKSUM=1`) |

The `.pt` file is kept as a separate file (not tracked in git — see
`.gitignore`) and is copied into the container image at build time.

Architecture (read from the loaded checkpoint): `BondMessagePassing` (directed
edge messages, depth 3, hidden 300, input = 72-dim atom + 14-dim bond
features) → `NormAggregation` (sum of atom vectors / 100) → no batch norm →
`BinaryClassificationFFN` (300 → 300, ReLU, → 631, sigmoid). Featurizer: chemprop default
`SimpleMoleculeMolGraphFeaturizer` with the v2 `MultiHotAtomFeaturizer`.

Verify manually:

```bash
cd models && sha256sum -c SHA256SUMS
```
