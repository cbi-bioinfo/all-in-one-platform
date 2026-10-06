"""MTDNN inference engine.

Pipeline per molecule: canonical SMILES -> SE encoder (GRU-VAE translation
model, IBM/multitask-toxicity SE_featurization; 128-dim mu) -> MTDNN (2 shared
+ per-task layers) -> 631 sigmoid probabilities. Inference runs in float64
with deterministic kernels so repeated runs agree far inside the 1e-6
probability tolerance.
"""
import hashlib
import logging
import os
import random
import threading
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

from .errors import ToxError

log = logging.getLogger("mtdnn_tox")

THRESHOLD = 0.5


class MTDNN(nn.Module):
    """2 shared layers (2048 -> 1024) + per-task layers (512 -> 256 -> 1)."""

    def __init__(self, input_shape: int, all_tasks: list[str]):
        super().__init__()
        self.all_tasks = all_tasks
        self.shared_1 = nn.Linear(input_shape, 2048)
        self.batchnorm_1 = nn.BatchNorm1d(2048)
        self.shared_2 = nn.Linear(2048, 1024)
        self.batchnorm_2 = nn.BatchNorm1d(1024)
        self.hidden_3 = nn.ModuleList([nn.Linear(1024, 512) for _ in all_tasks])
        self.batchnorm_3 = nn.ModuleList([nn.BatchNorm1d(512) for _ in all_tasks])
        self.hidden_4 = nn.ModuleList([nn.Linear(512, 256) for _ in all_tasks])
        self.batchnorm_4 = nn.ModuleList([nn.BatchNorm1d(256) for _ in all_tasks])
        self.output = nn.ModuleList([nn.Linear(256, 1) for _ in all_tasks])
        self.leakyReLU = nn.LeakyReLU(0.05)

    def forward(self, x):
        x = self.leakyReLU(self.batchnorm_1(self.shared_1(x)))
        x = self.leakyReLU(self.batchnorm_2(self.shared_2(x)))
        out = []
        for i in range(len(self.output)):
            t = self.leakyReLU(self.batchnorm_3[i](self.hidden_3[i](x)))
            t = self.leakyReLU(self.batchnorm_4[i](self.hidden_4[i](t)))
            out.append(torch.sigmoid(self.output[i](t)))
        return torch.cat(out, dim=1)


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
        self.lock = threading.Lock()  # serve mode: /predict and the job worker share one model
        self.device = resolve_device(cfg.device)
        se_files = [cfg.se_encoder_dir / n for n in ("model.pt", "config.nb", "vocab.nb")]
        for f in [cfg.model_path, *se_files]:
            if not f.is_file():
                raise ToxError("E-MODEL-001", f"missing {f}")
        digests = {}
        if cfg.verify_checksum:
            log.info("Verifying model checksums ...")
            digests = verify_checksums(cfg.model_dir, [cfg.model_path, *se_files])

        try:
            from moses.trans.model import TranslationModel
            se_config = torch.load(se_files[1], map_location="cpu", weights_only=False)
            self.vocab = torch.load(se_files[2], map_location="cpu", weights_only=False)
            se = TranslationModel(self.vocab, se_config)
            se.load_state_dict(torch.load(se_files[0], map_location="cpu"))
            self.se = se.double().to(self.device).eval()

            ckpt = torch.load(cfg.model_path, map_location="cpu")
            self.tasks: list[str] = list(ckpt["tasks"])
            model = MTDNN(input_shape=ckpt.get("emb_dim", 128), all_tasks=self.tasks)
            model.load_state_dict(ckpt["state_dict"])
            self.model = model.double().to(self.device).eval()
        except ToxError:
            raise
        except Exception as e:
            raise ToxError("E-MODEL-001", f"{type(e).__name__}: {e}")

        self.model_sha256 = digests.get(cfg.model_path) or sha256(cfg.model_path)
        log.info("Model loaded: %d tasks, device=%s", len(self.tasks), self.device)

    def encoder_warnings(self, smiles: str) -> list[str]:
        """The SE tokenizer silently drops characters it has no pattern for
        (e.g. '.', '/', '\\', metal symbols) and maps tokens outside its
        vocabulary (e.g. '@') to <unk>."""
        from moses.utils import smiles_tokenize
        tokens = smiles_tokenize(smiles)
        if "".join(tokens) != smiles or any(t not in self.vocab.c2i for t in tokens):
            return ["W-ENC-001"]
        return []

    @torch.no_grad()
    def encode(self, smiles: str) -> torch.Tensor:
        tensor = self.se.string2tensor(smiles)
        if tensor.numel() <= 2:  # only <bos>/<eos> left
            raise ToxError("E-MODEL-003", smiles)
        mu, *_ = self.se.forward_encoder([tensor])
        return mu[0]

    @torch.no_grad()
    def predict(self, embeddings: list[torch.Tensor]) -> np.ndarray:
        """(n, 128) embeddings -> (n, n_tasks) float64 probabilities."""
        x = torch.stack(embeddings).to(self.device, dtype=torch.float64)
        return self.model(x).cpu().numpy()
