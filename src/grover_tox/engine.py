"""GROVER inference engine (fine-tuned GROVER-base, 631 tasks).

Molecules are featurized with the vendored GROVER `MolGraph` (atom/bond
features exactly as in training) from the SMILES string that was parsed, and
scored by the vendored `GroverFinetuneTask` (atom-view and bond-view heads,
sigmoid outputs averaged).

Batch independence: GROVER pads each atom's incoming-bond list to the largest
atom degree in the batch with a padding row whose embedding is non-zero after
the first LayerNorm, so the predicted probability of a molecule depends on the
other molecules in its batch. This engine fixes the padding width per
molecule: max(PAD_WIDTH, the molecule's own largest atom degree), with
PAD_WIDTH = 4, the value that occurred in about 95 % of the size-32 training
batches. Molecules whose own maximum degree is <= 4 are batched together at
width 4; molecules with a higher degree are run on their own. Each
molecule's result therefore depends only on the molecule itself.
"""
import hashlib
import json
import logging
import os
import random
import threading
from argparse import Namespace
from pathlib import Path
from typing import List

import numpy as np
import torch
from rdkit.Chem import rdchem

from .errors import ToxError

log = logging.getLogger("grover_tox")

THRESHOLD = 0.5
PAD_WIDTH = 4
# Molecules per forward pass (bounds GPU memory; results do not depend on it).
SUB_BATCH = 32
_STD_BONDS = {rdchem.BondType.SINGLE, rdchem.BondType.DOUBLE,
              rdchem.BondType.TRIPLE, rdchem.BondType.AROMATIC}


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


def verify_checksums(model_dir: Path, files: List[Path]) -> dict:
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


def _fixed_width_batch(mol_graphs, width: int):
    """BatchMolGraph whose a2b padding width is `width` instead of the
    batch's largest atom degree (otherwise identical to the vendored class)."""
    from grover.data.molgraph import BatchMolGraph
    bmg = BatchMolGraph.__new__(BatchMolGraph)
    bmg.smiles_batch = [g.smiles for g in mol_graphs]
    bmg.n_mols = len(mol_graphs)
    from grover.data.molgraph import get_atom_fdim, get_bond_fdim
    bmg.atom_fdim = get_atom_fdim()
    bmg.bond_fdim = get_bond_fdim() + bmg.atom_fdim
    n_atoms, n_bonds = 1, 1
    a_scope, b_scope = [], []
    f_atoms = [[0] * bmg.atom_fdim]
    f_bonds = [[0] * bmg.bond_fdim]
    a2b, b2a, b2revb = [[]], [0], [0]
    for g in mol_graphs:
        f_atoms.extend(g.f_atoms)
        f_bonds.extend(g.f_bonds)
        for a in range(g.n_atoms):
            a2b.append([b + n_bonds for b in g.a2b[a]])
        for b in range(g.n_bonds):
            b2a.append(n_atoms + g.b2a[b])
            b2revb.append(n_bonds + g.b2revb[b])
        a_scope.append((n_atoms, g.n_atoms))
        b_scope.append((n_bonds, g.n_bonds))
        n_atoms += g.n_atoms
        n_bonds += g.n_bonds
    actual = max(1, max(len(x) for x in a2b))
    if actual > width:
        raise ValueError(f"batch needs padding width {actual} > {width}")
    bmg.n_atoms, bmg.n_bonds = n_atoms, n_bonds
    bmg.max_num_bonds = width
    bmg.f_atoms = torch.FloatTensor(f_atoms)
    bmg.f_bonds = torch.FloatTensor(f_bonds)
    bmg.a2b = torch.LongTensor([x + [0] * (width - len(x)) for x in a2b])
    bmg.b2a = torch.LongTensor(b2a)
    bmg.b2revb = torch.LongTensor(b2revb)
    bmg.b2b = None
    bmg.a2a = bmg.b2a[bmg.a2b]
    bmg.a_scope = torch.LongTensor(a_scope)
    bmg.b_scope = torch.LongTensor(b_scope)
    return bmg


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
            from grover.util.utils import build_model
            mc = json.loads(cfg.model_config.read_text())
            self.tasks: List[str] = list(mc["tasks"])
            state = torch.load(cfg.model_path, map_location="cpu", weights_only=False)
            args: Namespace = state["args"]
            args.cuda = self.device.type == "cuda"
            args.bond_drop_rate = 0
            args.no_cache = True
            if list(args.task_names) != self.tasks:
                raise ValueError("task list in config does not match the checkpoint")
            if state.get("data_scaler") is not None:
                raise ValueError("checkpoint carries a target scaler (regression) — not supported")
            model = build_model(args)
            missing = set(model.state_dict()) - set(state["state_dict"])
            unexpected = set(state["state_dict"]) - set(model.state_dict())
            if missing or unexpected:
                raise ValueError(f"state_dict mismatch: missing={sorted(missing)[:3]} unexpected={sorted(unexpected)[:3]}")
            model.load_state_dict(state["state_dict"])
            self.model = model.double().to(self.device).eval()
            self.args = args
        except ToxError:
            raise
        except Exception as e:
            raise ToxError("E-MODEL-001", f"{type(e).__name__}: {e}")
        log.info("Model loaded: %d tasks, device=%s", len(self.tasks), self.device)

    def encode(self, prep):
        """Return (MolGraph, warnings) built from the SMILES string that was parsed."""
        from grover.data.molgraph import MolGraph
        mol = prep.mol
        if mol is None or mol.GetNumAtoms() == 0:
            raise ToxError("E-MODEL-003")
        if mol.GetNumHeavyAtoms() == 0:
            raise ToxError("E-INPUT-012")
        charges = [a.GetFormalCharge() for a in mol.GetAtoms()]
        bad = [c for c in charges if c > 5 or c < -6]
        if bad:
            # The vendored one-hot uses the raw charge as a list index.
            raise ToxError("E-INPUT-013", f"formal charge {bad[0]:+d}")
        warnings = []
        if any(b.GetBondType() not in _STD_BONDS for b in mol.GetBonds()):
            warnings.append("W-FEAT-001")
        if any(abs(c) > 2 for c in charges) or any(a.GetAtomicNum() > 100 for a in mol.GetAtoms()):
            warnings.append("W-FEAT-002")
        try:
            g = MolGraph(prep.parse_smiles, self.args)
        except Exception as e:
            raise ToxError("E-MODEL-003", f"{type(e).__name__}: {e}")
        g.pad_width = max(PAD_WIDTH, max((len(x) for x in g.a2b), default=0))
        return g, warnings

    @torch.no_grad()
    def predict(self, graphs: list) -> np.ndarray:
        """MolGraphs -> (n, n_tasks) float64 probabilities, batch-independent."""
        out = np.zeros((len(graphs), len(self.tasks)), dtype=np.float64)
        groups: dict = {}
        for i, g in enumerate(graphs):
            key = PAD_WIDTH if g.pad_width == PAD_WIDTH else ("solo", i)
            groups.setdefault(key, []).append(i)
        sub = []
        for key, idx in groups.items():
            for start in range(0, len(idx), SUB_BATCH):
                sub.append((key, idx[start:start + SUB_BATCH]))
        for key, idx in sub:
            width = PAD_WIDTH if key == PAD_WIDTH else graphs[idx[0]].pad_width
            bmg = _fixed_width_batch([graphs[i] for i in idx], width)
            f_atoms, f_bonds, a2b, b2a, b2revb, a_scope, b_scope, a2a = bmg.get_components()
            batch = (f_atoms.double(), f_bonds.double(), a2b, b2a, b2revb, a_scope, b_scope, a2a)
            dev = self.device
            batch = tuple(t.to(dev) if torch.is_tensor(t) and k not in (5, 6) else t for k, t in enumerate(batch))
            preds = self.model(batch, [None] * len(idx))
            out[idx] = preds.double().cpu().numpy()
        return out
