"""FP-GNN inference engine (fingerprint branch + graph-attention branch).

For every molecule:
  * fingerprint branch — MACCS (167) + ErG (441, fuzzIncrement 0.3, paths 1–21)
    + PubChem (881) = 1,489 values -> Linear 512 -> ReLU -> Linear 300
  * graph branch — 133-dim one-hot atom features, dense adjacency without
    self-loops; 8 attention heads (133 -> 60, ELU) concatenated, an output
    attention layer (480 -> 300), ELU, log-softmax over features, mean over atoms
  * each branch -> Linear 300 -> ReLU, concatenated (600) -> Linear 300 -> ReLU
    -> Linear 631 -> sigmoid
This reproduces the computation of the trained model so that the stored
weights load unchanged. Inference runs in float64.
"""
import hashlib
import json
import logging
import os
import random
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from rdkit import Chem
from rdkit.Chem import AllChem, rdchem, rdmolops

from .errors import ToxError

log = logging.getLogger("fpgnn_tox")

THRESHOLD = 0.5
ATOM_DIM = 133

# Atom encoder categories (each block also has one trailing 'other' slot).
_ATOMIC_NUM = list(range(100))          # value used: atomic number - 1
_DEGREE = [0, 1, 2, 3, 4, 5]            # total degree (incl. H)
_CHARGE = [-1, -2, 1, 2, 0]
_CHIRAL = [0, 1, 2, 3]                  # int(ChiralType)
_NUM_H = [0, 1, 2, 3, 4]
_HYBRID = [int(h) for h in (rdchem.HybridizationType.SP, rdchem.HybridizationType.SP2,
                            rdchem.HybridizationType.SP3, rdchem.HybridizationType.SP3D,
                            rdchem.HybridizationType.SP3D2)]


def _one_hot(value, choices) -> tuple[list, bool]:
    vec = [0] * (len(choices) + 1)
    known = value in choices
    vec[choices.index(value) if known else -1] = 1
    return vec, known


def atom_features(atom) -> tuple[list, bool]:
    blocks = [_one_hot(atom.GetAtomicNum() - 1, _ATOMIC_NUM),
              _one_hot(atom.GetTotalDegree(), _DEGREE),
              _one_hot(atom.GetFormalCharge(), _CHARGE),
              _one_hot(int(atom.GetChiralTag()), _CHIRAL),
              _one_hot(int(atom.GetTotalNumHs()), _NUM_H),
              _one_hot(int(atom.GetHybridization()), _HYBRID)]
    feat = [x for vec, _ in blocks for x in vec]
    feat += [1 if atom.GetIsAromatic() else 0, atom.GetMass() * 0.01]
    return feat, all(known for _, known in blocks)


def fingerprint(mol) -> list:
    from pybiomed.PubChemFingerprints import calcPubChemFingerAll
    fp = list(AllChem.GetMACCSKeysFingerprint(mol))
    fp += list(AllChem.GetErGFingerprint(mol, fuzzIncrement=0.3, maxPath=21, minPath=1))
    fp += list(calcPubChemFingerAll(Chem.AddHs(mol)))
    return fp


# ── network (parameter names match the stored state_dict) ──────────────────

class AttentionHead(nn.Module):
    def __init__(self, n_in: int, n_out: int, concat: bool):
        super().__init__()
        self.n_out = n_out
        self.concat = concat
        self.W = nn.Parameter(torch.zeros(n_in, n_out))
        self.a = nn.Parameter(torch.zeros(2 * n_out, 1))
        self.leaky = nn.LeakyReLU(0.2)

    def forward(self, h, adj):
        wh = h @ self.W                                   # (N, n_out)
        # score(i, j) = a^T [Wh_i || Wh_j]
        e = self.leaky(wh @ self.a[: self.n_out] + (wh @ self.a[self.n_out:]).T)
        e = torch.where(adj > 0, e, torch.full_like(e, -9e15))
        out = torch.softmax(e, dim=1) @ wh
        return nn.functional.elu(out) if self.concat else out


class GraphEncoder(nn.Module):
    def __init__(self, n_heads: int, n_hid: int, hidden: int):
        super().__init__()
        for i in range(n_heads):
            self.add_module(f"attention_{i}", AttentionHead(ATOM_DIM, n_hid, concat=True))
        self.n_heads = n_heads
        self.out_att = AttentionHead(n_hid * n_heads, hidden, concat=False)

    def forward(self, h, adj):
        h = torch.cat([getattr(self, f"attention_{i}")(h, adj) for i in range(self.n_heads)], dim=1)
        h = nn.functional.elu(self.out_att(h, adj))
        return torch.log_softmax(h, dim=1).mean(dim=0)


class _Wrap(nn.Module):
    def __init__(self, **children):
        super().__init__()
        for k, v in children.items():
            self.add_module(k, v)


class FingerprintEncoder(nn.Module):
    def __init__(self, fp_dim: int, fp_hid: int, hidden: int):
        super().__init__()
        self.fc1 = nn.Linear(fp_dim, fp_hid)
        self.fc2 = nn.Linear(fp_hid, hidden)

    def forward(self, fp):
        return self.fc2(torch.relu(self.fc1(fp)))


class FPGNNNet(nn.Module):
    def __init__(self, hidden: int, fp_hid: int, n_hid: int, n_heads: int, gat_scale: float, n_tasks: int):
        super().__init__()
        gat_dim = int((hidden * 2 * gat_scale) // 1)
        self.encoder3 = _Wrap(encoder=_Wrap(encoder=GraphEncoder(n_heads, n_hid, hidden)))
        self.encoder2 = FingerprintEncoder(1489, fp_hid, hidden)
        self.fc_gat = nn.Linear(hidden, gat_dim)
        self.fc_fpn = nn.Linear(hidden, hidden * 2 - gat_dim)
        self.ffn = nn.Sequential(nn.Identity(), nn.Linear(hidden * 2, hidden), nn.ReLU(),
                                 nn.Identity(), nn.Linear(hidden, n_tasks))

    def forward(self, graphs, fps):
        enc = self.encoder3.encoder.encoder
        g = torch.stack([enc(h, adj) for h, adj in graphs])
        f = self.encoder2(fps)
        x = torch.cat([torch.relu(self.fc_gat(g)), torch.relu(self.fc_fpn(f))], dim=1)
        return torch.sigmoid(self.ffn(x))


# ── runtime ────────────────────────────────────────────────────────────────

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
            if mc.get("fp_type") != "mixed" or mc.get("dataset_type") != "classification":
                raise ValueError(f"unsupported configuration {mc.get('fp_type')}/{mc.get('dataset_type')}")
            self.tasks: list[str] = list(mc["tasks"])
            net = FPGNNNet(mc["hidden_size"], mc["fp_2_dim"], mc["nhid"], mc["nheads"],
                           mc["gat_scale"], len(self.tasks))
            # The checkpoint also pickles the training argparse.Namespace, so
            # it needs weights_only=False; its SHA-256 was verified above.
            state = torch.load(cfg.model_path, map_location="cpu", weights_only=False)
            net.load_state_dict(state["state_dict"])
            self.model = net.double().to(self.device).eval()
        except Exception as e:
            raise ToxError("E-MODEL-001", f"{type(e).__name__}: {e}")
        log.info("Model loaded: %d tasks, device=%s", len(self.tasks), self.device)

    def encode(self, mol):
        """Return ((atom features, adjacency, fingerprint), warnings)."""
        if mol is None or mol.GetNumAtoms() == 0:
            raise ToxError("E-MODEL-003")
        feats, all_known = zip(*(atom_features(a) for a in mol.GetAtoms()))
        warnings = []
        if not all(all_known):
            warnings.append("W-FEAT-001")
        adj = rdmolops.GetAdjacencyMatrix(mol).astype(np.float64)
        if (adj.sum(axis=1) == 0).any():
            warnings.append("W-FEAT-002")
        return (np.asarray(feats, dtype=np.float64), adj, np.asarray(fingerprint(mol), dtype=np.float64)), warnings

    @torch.no_grad()
    def predict(self, items: list) -> np.ndarray:
        """Encoded molecules -> (n, n_tasks) float64 probabilities."""
        dev = self.device
        graphs = [(torch.from_numpy(h).to(dev), torch.from_numpy(adj).to(dev)) for h, adj, _ in items]
        fps = torch.from_numpy(np.stack([fp for _, _, fp in items])).to(dev)
        return self.model(graphs, fps).cpu().numpy()
