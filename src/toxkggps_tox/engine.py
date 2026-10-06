"""ToxKG-GPS inference engine (molecule-only GPS-GINE, no knowledge graph).

Each molecule becomes a PyG graph with 12 atom features and 6 bond features —
the exact featurization used in training — and one multi-task network scores
all 631 tasks: 3 GPS blocks (GINEConv local message passing + per-molecule
multi-head self-attention), mean pooling, LayerNorm + linear head. Inference
runs in float64 with deterministic kernels.
"""
import hashlib
import json
import logging
import os
import random
import threading
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from rdkit.Chem import rdchem

from .errors import ToxError

log = logging.getLogger("toxkggps_tox")

THRESHOLD = 0.5
EDGE_DIM = 6
_HYB = {rdchem.HybridizationType.SP: 0, rdchem.HybridizationType.SP2: 1,
        rdchem.HybridizationType.SP3: 2, rdchem.HybridizationType.SP3D: 3,
        rdchem.HybridizationType.SP3D2: 4}
_BOND = {rdchem.BondType.SINGLE: [1, 0, 0, 0], rdchem.BondType.DOUBLE: [0, 1, 0, 0],
         rdchem.BondType.TRIPLE: [0, 0, 1, 0], rdchem.BondType.AROMATIC: [0, 0, 0, 1]}


def _atom_features(atom) -> list:
    h = _HYB.get(atom.GetHybridization(), 5)
    return [atom.GetAtomicNum(), atom.GetDegree(), atom.GetFormalCharge(),
            atom.GetTotalNumHs(), int(atom.GetIsAromatic()), int(atom.IsInRing()),
            int(h == 0), int(h == 1), int(h == 2), int(h == 3), int(h == 4), int(h == 5)]


class LGBlock(nn.Module):
    """Local (GINEConv) + global (per-molecule multi-head attention) GPS block."""

    def __init__(self, hidden: int, heads: int, drop: float):
        super().__init__()
        from torch_geometric.nn import GINEConv
        mlp = nn.Sequential(nn.Linear(hidden, hidden), nn.ReLU(), nn.Linear(hidden, hidden))
        self.gine = GINEConv(mlp, edge_dim=hidden)
        self.norm1 = nn.LayerNorm(hidden)
        self.mha = nn.MultiheadAttention(hidden, heads, dropout=drop, batch_first=True)
        self.norm2 = nn.LayerNorm(hidden)
        self.ffn = nn.Sequential(nn.Linear(hidden, hidden * 2), nn.GELU(),
                                 nn.Dropout(drop), nn.Linear(hidden * 2, hidden))

    def forward(self, x, edge_index, ea, batch):
        from torch_geometric.utils import to_dense_batch
        x = self.norm1(x + self.gine(x, edge_index, ea))
        x_dense, mask = to_dense_batch(x, batch)
        h, _ = self.mha(x_dense, x_dense, x_dense, key_padding_mask=~mask, need_weights=False)
        x = x + h[mask]
        return x + self.ffn(self.norm2(x))


class GPSBench(nn.Module):
    def __init__(self, in_dim: int, hidden: int, heads: int, layers: int, n_tasks: int, drop: float):
        super().__init__()
        self.node_proj = nn.Linear(in_dim, hidden)
        self.edge_proj = nn.Linear(EDGE_DIM, hidden)
        self.blocks = nn.ModuleList([LGBlock(hidden, heads, drop) for _ in range(layers)])
        self.head = nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, n_tasks))

    def forward(self, data):
        from torch_geometric.nn import global_mean_pool
        x = self.node_proj(data.x)
        ea = self.edge_proj(data.edge_attr)
        for blk in self.blocks:
            x = blk(x, data.edge_index, ea, data.batch)
        return self.head(global_mean_pool(x, data.batch))


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
    expected = {}
    for line in sums_file.read_text().splitlines():
        if line.strip():
            digest, name = line.split(maxsplit=1)
            expected[name.lstrip("*").strip()] = digest
    digests = {}
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
        self.lock = threading.Lock()  # serve mode: /predict and the job worker share one model
        self.device = resolve_device(cfg.device)
        for f in (cfg.model_path, cfg.model_config):
            if not f.is_file():
                raise ToxError("E-MODEL-001", f"missing {f}")
        digests = {}
        if cfg.verify_checksum:
            log.info("Verifying model checksums ...")
            digests = verify_checksums(cfg.model_dir, [cfg.model_path, cfg.model_config])
        self.model_sha256 = digests.get(cfg.model_path) or sha256(cfg.model_path)

        try:
            mc = json.loads(cfg.model_config.read_text())
            self.tasks: list[str] = list(mc["tasks"])
            model = GPSBench(mc["in_dim"], mc["hidden"], mc["heads"], mc["layers"], len(self.tasks), mc["dropout"])
            model.load_state_dict(torch.load(cfg.model_path, map_location="cpu"))
            self.model = model.double().to(self.device).eval()
        except Exception as e:
            raise ToxError("E-MODEL-001", f"{type(e).__name__}: {e}")
        log.info("Model loaded: %d tasks, device=%s", len(self.tasks), self.device)

    def encode(self, mol):
        """Return (graph, warnings) for an RDKit molecule — same features as training."""
        from torch_geometric.data import Data
        if mol is None or mol.GetNumAtoms() == 0:
            raise ToxError("E-MODEL-003")
        x = torch.tensor([_atom_features(a) for a in mol.GetAtoms()], dtype=torch.float64)
        src, dst, ea, warnings = [], [], [], []
        for bond in mol.GetBonds():
            bt = _BOND.get(bond.GetBondType())
            if bt is None:
                bt = [0, 0, 0, 0]
                if "W-FEAT-001" not in warnings:
                    warnings.append("W-FEAT-001")
            f = bt + [int(bond.GetIsConjugated()), int(bond.IsInRing())]
            i, j = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
            src += [i, j]
            dst += [j, i]
            ea += [f, f]
        edge_index = torch.tensor([src, dst], dtype=torch.long) if src else torch.zeros((2, 0), dtype=torch.long)
        edge_attr = torch.tensor(ea, dtype=torch.float64) if ea else torch.zeros((0, EDGE_DIM), dtype=torch.float64)
        return Data(x=x, edge_index=edge_index, edge_attr=edge_attr), warnings

    @torch.no_grad()
    def predict(self, graphs: list) -> np.ndarray:
        """Graphs -> (n, n_tasks) float64 probabilities."""
        from torch_geometric.data import Batch
        batch = Batch.from_data_list(graphs).to(self.device)
        return torch.sigmoid(self.model(batch)).cpu().numpy()
