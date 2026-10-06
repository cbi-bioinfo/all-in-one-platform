# Model weights

| File | Size (bytes) | SHA-256 | Content |
|---|---:|---|---|
| `grover_trainset_seed2.pt` | 195,924,310 | `2d6a3350a2d665dfa552427ba1b6f60cf2f07635641c2a7718f254d16076fc9e` | Full GROVER fine-tuning checkpoint: `{'args', 'state_dict', 'data_scaler': None, 'features_scaler': None}`, 48,963,696 parameters |
| `grover_trainset_seed2_config.json` | 17,538 | `551d285bbcac4efeb178af373673105a0193f53728a1e4ac8747ca6f641148b7` | Task list (631 names in output order) and architecture summary |
| `SHA256SUMS` | — | — | Checksums of the two files above, verified at container start-up (`VERIFY_CHECKSUM=1`) |

The checkpoint was fine-tuned from GROVER-base (`grover_base.pt`, upstream
release) on the trainset holdout **seed 2** training split. The pre-trained
encoder weights are part of this checkpoint, so `grover_base.pt` is **not**
needed at inference and is not shipped.

Architecture (from the checkpoint `args`): `dualtrans` backbone, hidden size 800,
message-passing depth 6, 1 multi-head attention block with 4 heads, PReLU,
embedding output `both` (atom-view and bond-view), two readout heads
(mean pooling → FFN 800 → 200 → 631), outputs averaged after sigmoid.

The `.pt` file is kept as a separate file (not tracked in git — `.gitignore`)
and is copied into the image at build time. Verify manually:

```bash
cd models && sha256sum -c SHA256SUMS
```
