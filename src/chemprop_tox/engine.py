"""Chemprop (D-MPNN) inference engine.

Each molecule is featurized by chemprop's default SimpleMoleculeMolGraphFeaturizer
(72-dim multi-hot atom features, 14-dim bond features) — the featurizer used by
`chemprop train` / `chemprop predict` — and scored by the trained MPNN:
directed bond message passing (depth 3) -> norm aggregation -> feed-forward
head with 631 sigmoid outputs. Inference runs in float64 with deterministic
kernels.
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
from rdkit.Chem.rdchem import BondType

from .errors import ToxError

log = logging.getLogger("chemprop_tox")

THRESHOLD = 0.5
_KNOWN_BONDS = (BondType.SINGLE, BondType.DOUBLE, BondType.TRIPLE, BondType.AROMATIC)


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
            from chemprop import data, featurizers
            from chemprop.models.utils import load_model

            mc = json.loads(cfg.model_config.read_text())
            self.tasks: list[str] = list(mc["tasks"])
            model = load_model(str(cfg.model_path), False)
            if model.predictor.n_tasks != len(self.tasks):
                raise ValueError(f"model has {model.predictor.n_tasks} outputs, config lists {len(self.tasks)} tasks")
            self.model = model.double().to(self.device).eval()
            self._featurizer = featurizers.SimpleMoleculeMolGraphFeaturizer()
            if self._featurizer.atom_fdim + self._featurizer.bond_fdim != model.message_passing.W_i.in_features:
                raise ValueError("featurizer dimensions do not match the model input")
            self._data = data
            af = self._featurizer.atom_featurizer
            self._known = {"atomic_num": set(af.atomic_nums), "degree": set(af.degrees),
                           "formal_charge": set(af.formal_charges), "chiral_tag": set(af.chiral_tags),
                           "num_Hs": set(af.num_Hs), "hybridization": set(af.hybridizations)}
        except Exception as e:
            raise ToxError("E-MODEL-001", f"{type(e).__name__}: {e}")
        log.info("Model loaded: %d tasks, device=%s", len(self.tasks), self.device)

    def encode(self, mol):
        """Return (datapoint, warnings) for an RDKit molecule."""
        if mol is None or mol.GetNumAtoms() == 0:
            raise ToxError("E-MODEL-003")
        k, warnings = self._known, []
        for a in mol.GetAtoms():
            if (a.GetAtomicNum() not in k["atomic_num"] or a.GetTotalDegree() not in k["degree"]
                    or a.GetFormalCharge() not in k["formal_charge"]
                    or int(a.GetChiralTag()) not in k["chiral_tag"]
                    or int(a.GetTotalNumHs()) not in k["num_Hs"]
                    or a.GetHybridization() not in k["hybridization"]):
                warnings.append("W-FEAT-001")
                break
        if any(b.GetBondType() not in _KNOWN_BONDS for b in mol.GetBonds()):
            warnings.append("W-FEAT-002")
        return self._data.MoleculeDatapoint(mol=mol), warnings

    @torch.no_grad()
    def predict(self, datapoints: list) -> np.ndarray:
        """Datapoints -> (n, n_tasks) float64 probabilities."""
        dataset = self._data.MoleculeDataset(datapoints, self._featurizer)
        batch = self._data.collate_batch([dataset[i] for i in range(len(dataset))])
        bmg = batch.bmg
        bmg.V = bmg.V.double()
        bmg.E = bmg.E.double()
        bmg.to(self.device)
        return self.model(bmg, None, None).cpu().numpy()
