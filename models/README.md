# Model weights

One multi-task network scores all 631 trainset tasks. The submitted weights are
the trainset holdout **seed 0** run (best validation macro AUROC of 5 seeds,
also best on the untouched test split).

| File | Size (bytes) | SHA-256 | Content |
|---|---:|---|---|
| `gps_trainset_seed0.pt` | 2,540,928 | `95ac41f79b5ca5476cc040c670ca900569a51ead5daf79e0457162c827a294d4` | PyTorch `state_dict` of `GPSBench` (630,263 parameters) |
| `gps_trainset_seed0_config.json` | 17,250 | `b0a34a8c0a41aee3bf39b41fa5dbf15b16a1a1d11eb211a350acf435e6a3596b` | `in_dim` 12, `hidden` 128, `heads` 4, `layers` 3, `dropout` 0.1, `tasks` (631 names in output order) |
| `SHA256SUMS` | — | — | Checksums of the two files above; verified at container start-up (`VERIFY_CHECKSUM=1`) |

The `.pt` file is kept as a separate file (not tracked in git — see
`.gitignore`) and is copied into the container image at build time.

Architecture (`GPSBench`): node projection 12 → 128, edge projection 6 → 128;
3 GPS blocks, each = GINEConv local message passing (2-layer MLP) + LayerNorm,
per-molecule multi-head self-attention (4 heads), feed-forward 128 → 256 → 128
(GELU) with LayerNorm; global mean pooling; LayerNorm + linear head → 631
logits. The model uses the molecular graph only — no knowledge-graph data.

Verify manually:

```bash
cd models && sha256sum -c SHA256SUMS
```
