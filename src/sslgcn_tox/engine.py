"""SSL-GCN inference engine.

One GCN per task (dgllife GCNPredictor, Mean-Teacher teacher weights). Each
molecule becomes a DGL graph with self-loops and 74-dim CanonicalAtomFeaturizer
node features — exactly the featurization used in training — and every task
model scores the same batched graph. Inference runs in float64 with
deterministic kernels so repeated runs agree far inside the 1e-6 tolerance.
"""
import hashlib
import json
import logging
import os
import random
from pathlib import Path

import numpy as np
import torch

from .errors import ToxError

log = logging.getLogger("sslgcn_tox")

THRESHOLD = 0.5
# One-hot blocks of CanonicalAtomFeaturizer (74 dims): an atom whose value is
# outside a block's allowed set is silently encoded as all zeros in that block.
ONE_HOT_BLOCKS = {"element": (0, 43), "degree": (43, 54), "implicit_valence": (54, 61),
                  "hybridization": (63, 68), "total_num_H": (69, 74)}


def set_determinism(seed: int):
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.use_deterministic_algorithms(True, warn_only=True)


def resolve_device(name: str) -> torch.device:
    if name == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        log.warning("No GPU visible — falling back to CPU (set DEVICE=cpu to silence this warning)")
        return torch.device("cpu")
    if name == "cuda":
        if not torch.cuda.is_available():
            raise ToxError("E-SYS-002")
        return torch.device("cuda")
    if name == "cpu":
        return torch.device("cpu")
    raise ToxError("E-SYS-004", f"DEVICE={name!r} (use auto, cuda or cpu)")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify_checksums(model_dir: Path) -> str:
    """Check every file listed in SHA256SUMS; return the digest of SHA256SUMS
    itself, which identifies the full weight set."""
    sums_file = model_dir / "SHA256SUMS"
    if not sums_file.is_file():
        raise ToxError("E-MODEL-002", f"{sums_file} not found")
    for line in sums_file.read_text().splitlines():
        if not line.strip():
            continue
        digest, name = line.split(maxsplit=1)
        path = model_dir / name.lstrip("*").strip()
        if not path.is_file():
            raise ToxError("E-MODEL-001", f"missing {path}")
        if sha256(path) != digest:
            raise ToxError("E-MODEL-002", name.strip())
    return sha256(sums_file)


class Predictor:
    def __init__(self, cfg):
        set_determinism(cfg.seed)
        self.device = resolve_device(cfg.device)
        manifest = cfg.model_dir / "tasks.json"
        if not manifest.is_file():
            raise ToxError("E-MODEL-001", f"missing {manifest}")
        if cfg.verify_checksum:
            log.info("Verifying model checksums ...")
            self.model_sha256 = verify_checksums(cfg.model_dir)
        else:
            self.model_sha256 = sha256(cfg.model_dir / "SHA256SUMS") if (cfg.model_dir / "SHA256SUMS").is_file() else None

        try:
            import torch.nn.functional as F
            from dgllife.model import GCNPredictor
            from dgllife.utils import CanonicalAtomFeaturizer, mol_to_bigraph

            self.tasks: list[str] = json.loads(manifest.read_text())["tasks"]
            self.models = []
            for task in self.tasks:
                d = cfg.model_dir / "tasks" / task
                c = json.loads((d / "configure.json").read_text())
                if c.get("model") != "GCN" or c.get("atom_featurizer_type") != "canonical":
                    raise ValueError(f"{task}: unsupported configuration {c.get('model')}/{c.get('atom_featurizer_type')}")
                n = c["num_gnn_layers"]
                model = GCNPredictor(
                    in_feats=c["in_node_feats"], hidden_feats=[c["gnn_hidden_feats"]] * n,
                    activation=[F.relu] * n, residual=[c["residual"]] * n,
                    batchnorm=[c["batchnorm"]] * n, dropout=[c["dropout"]] * n,
                    predictor_hidden_feats=c["predictor_hidden_feats"],
                    predictor_dropout=c["dropout"], n_tasks=c["n_tasks"])
                model.load_state_dict(torch.load(d / "model.pth", map_location="cpu")["model_state_dict"])
                self.models.append(model.double().to(self.device).eval())
            self._featurizer = CanonicalAtomFeaturizer()
            self._to_graph = mol_to_bigraph
        except ToxError:
            raise
        except Exception as e:
            raise ToxError("E-MODEL-001", f"{type(e).__name__}: {e}")
        log.info("Model loaded: %d task models, device=%s", len(self.tasks), self.device)

    def encode(self, mol):
        """Return (graph, warnings) for an RDKit molecule — the same graph
        dgllife's smiles_to_bigraph builds in training (self-loops, canonical
        atom order, no explicit H)."""
        g = self._to_graph(mol, add_self_loop=True, node_featurizer=self._featurizer, edge_featurizer=None)
        if g is None or g.num_nodes() == 0:
            raise ToxError("E-MODEL-003")
        h = g.ndata["h"]
        warnings = []
        for lo, hi in ONE_HOT_BLOCKS.values():
            if bool((h[:, lo:hi].sum(dim=1) != 1).any()):
                warnings.append("W-FEAT-001")
                break
        g.ndata["h"] = h.double()
        return g, warnings

    @torch.no_grad()
    def predict(self, graphs: list) -> np.ndarray:
        """Batched graphs -> (n, n_tasks) float64 probabilities."""
        import dgl
        bg = dgl.batch(graphs).to(self.device)
        h = bg.ndata["h"]
        out = [torch.sigmoid(m(bg, h)).squeeze(-1) for m in self.models]
        return torch.stack(out, dim=1).cpu().numpy()
