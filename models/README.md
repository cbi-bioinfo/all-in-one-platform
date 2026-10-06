# Model weights

One multi-task FP-GNN network scores all 631 trainset tasks. The submitted
weights are the trainset holdout **seed 0** run (best validation macro AUROC of
the 5 seeds).

| File | Size (bytes) | SHA-256 | Content |
|---|---:|---|---|
| `fpgnn_trainset_seed0.pt` | 6,738,926 | `5cb842f64c5885ecaa04e03b6657a9b8efac77c78bce387ff130226ee1022d3a` | Training checkpoint: `state_dict` (1,677,011 parameters) and the training `argparse.Namespace` (`args`) |
| `fpgnn_trainset_seed0_config.json` | 17,413 | `4df897e286913120698383e85d810adce07ce5e51e2e205cee2f7689d078d252` | `fp_type` mixed, `hidden_size` 300, `fp_2_dim` 512, `nhid` 60, `nheads` 8, `gat_scale` 0.5, dropout 0, `tasks` (631 names in output order) |
| `SHA256SUMS` | — | — | Checksums of the two files above; verified at container start-up (`VERIFY_CHECKSUM=1`) |

The `.pt` file is kept out of git (see `.gitignore`) and is copied into the
container image at build time. Because the checkpoint contains a pickled
`argparse.Namespace`, it is loaded with `weights_only=False` — only after its
SHA-256 has been verified.

Network (parameter names as stored):

* `encoder2` — fingerprint branch: Linear 1,489 → 512, ReLU, Linear 512 → 300
* `encoder3.encoder.encoder` — graph branch: 8 attention heads (`attention_0..7`,
  W 133 × 60, a 120 × 1, LeakyReLU 0.2, ELU) concatenated to 480, output head
  `out_att` (480 → 300), ELU, log-softmax over features, mean over atoms
* `fc_gat`, `fc_fpn` — 300 → 300 each, ReLU; concatenated to 600
* `ffn` — Linear 600 → 300, ReLU, Linear 300 → 631, sigmoid

Verify manually:

```bash
cd models && sha256sum -c SHA256SUMS
```
