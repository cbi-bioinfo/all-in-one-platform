"""SSL-GCN inference engine.

One GCN per task (dgllife GCNPredictor, Mean-Teacher teacher weights). Each
molecule becomes a DGL graph with self-loops and 74-dim CanonicalAtomFeaturizer
node features — exactly the featurization used in training — and every task
model scores the same batched graph. Inference runs in float64 with
deterministic kernels so repeated runs agree far inside the 1e-6 tolerance.
"""
import hashlib
import logging
import os
import random
import threading
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


def verify_checksums(model_dir: Path, files: list[Path]) -> dict[Path, str]:
    sums_file = model_dir / "SHA256SUMS"
    if not sums_file.is_file():
        raise ToxError("E-MODEL-002", f"{sums_file} not found")
    expected, digests = {}, {}
    for line in sums_file.read_text().splitlines():
        if line.strip():
            digest, name = line.split(maxsplit=1)
            expected[name.lstrip("*").strip()] = digest
    for f in files:
        rel = f.relative_to(model_dir).as_posix() if f.is_relative_to(model_dir) else f.name
        if rel not in expected:
            raise ToxError("E-MODEL-002", f"{rel} is not listed in SHA256SUMS")
        digests[f] = sha256(f)
        if digests[f] != expected[rel]:
            raise ToxError("E-MODEL-002", rel)
    return digests


class Predictor:
    def __init__(self, cfg):
        set_determinism(cfg.seed)
        self.device = resolve_device(cfg.device)
        self.lock = threading.Lock()  # serve mode: /predict and the job worker share one model
        if not cfg.model_path.is_file():
            raise ToxError("E-MODEL-001", f"missing {cfg.model_path}")
        digests = {}
        if cfg.verify_checksum:
            log.info("Verifying model checksums ...")
            digests = verify_checksums(cfg.model_dir, [cfg.model_path])

        try:
            import torch.nn.functional as F
            from dgllife.model import GCNPredictor
            from dgllife.utils import CanonicalAtomFeaturizer, mol_to_bigraph

            # Bundle: tasks (output order), tasks_without_model, the shared
            # configure.json of all task models, and one state_dict per task.
            bundle = torch.load(cfg.model_path, map_location="cpu", weights_only=True)
            self.tasks: list[str] = list(bundle["tasks"])
            self.tasks_without_model: list[str] = list(bundle["tasks_without_model"])
            c = bundle["config"]
            if c.get("model") != "GCN" or c.get("atom_featurizer_type") != "canonical":
                raise ValueError(f"unsupported configuration {c.get('model')}/{c.get('atom_featurizer_type')}")
            n = c["num_gnn_layers"]
            self.models = []
            for task in self.tasks:
                model = GCNPredictor(
                    in_feats=c["in_node_feats"], hidden_feats=[c["gnn_hidden_feats"]] * n,
                    activation=[F.relu] * n, residual=[c["residual"]] * n,
                    batchnorm=[c["batchnorm"]] * n, dropout=[c["dropout"]] * n,
                    predictor_hidden_feats=c["predictor_hidden_feats"],
                    predictor_dropout=c["dropout"], n_tasks=c["n_tasks"])
                model.load_state_dict(bundle["state_dicts"][task])
                self.models.append(model.double().to(self.device).eval())
            self._featurizer = CanonicalAtomFeaturizer()
            self._to_graph = mol_to_bigraph
        except ToxError:
            raise
        except Exception as e:
            raise ToxError("E-MODEL-001", f"{type(e).__name__}: {e}")
        self.model_sha256 = digests.get(cfg.model_path) or sha256(cfg.model_path)
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
