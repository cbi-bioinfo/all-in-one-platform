# Model weights

Weights are kept as separate files (not tracked in git — see `.gitignore`) and
are copied into the container image at build time. `SHA256SUMS` is tracked in
git and is checked by the container at start-up (`VERIFY_CHECKSUM=1`).

| File | Size (bytes) | SHA-256 | Content |
|---|---:|---|---|
| `mtdnn_trainset_seed0.pt` | 1,677,343,497 | `dac598cd0a982fb28c82ae733cc46cacd9250a5dcbb464e85bfa514e3982ac4d` | SE-MTDNN checkpoint: 631 tasks, 128-dim input, epoch 2 (lowest val loss), trained on trainset holdout seed0 train split |
| `se_encoder/model.pt` | 50,302,643 | `c5571eb0eb433ba55c88f849972f2b38ab5a68121b1941bc26ec8751ec6bcd18` | SE (SMILES Embedding) GRU-VAE translation model weights |
| `se_encoder/config.nb` | 3,114 | `e71d74e6b3d89bf77a56d1bbf45ed6aad025320cd4306d7263642c578a33c5d5` | SE model configuration (pickled `argparse.Namespace`) |
| `se_encoder/vocab.nb` | 7,151 | `0382796e629ac8aa953bca8684077a165daef1efe85799d5e1230c45a589e7ae` | SE tokenizer vocabulary (39 tokens) |
| `se_encoder/LICENSE` | 11,042 | — | Provenance and Apache-2.0 license of the SE encoder files |

Verify manually:

```bash
cd models && sha256sum -c SHA256SUMS
```

Checkpoint format (`torch.save` dict): `state_dict`, `tasks` (list of 631 task
names, output order), `emb_dim` (128), `epoch`, `val_loss`, `run_id`.
