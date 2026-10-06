"""Record-level processing shared by batch and serve modes."""
import logging

import numpy as np

from .engine import THRESHOLD
from .errors import ToxError
from .inputs import Record, prepare

log = logging.getLogger("chemprop_tox")
FORWARD_BATCH = 256


def run_records(predictor, records: list[Record], cfg) -> list[dict]:
    """Prepare, encode and predict every record. A failing record gets
    status='error' and never stops the others."""
    results, features, slots = [], [], []
    for rec in records:
        res = {
            "index": rec.index, "id": rec.record_id, "input_smiles": rec.input_smiles,
            "canonical_smiles": None, "status": "ok", "error": None, "warnings": [],
            "probabilities": None,
        }
        try:
            if rec.error is not None:
                raise rec.error
            prep = prepare(rec.input_smiles, cfg.standardize, cfg.max_smiles_length)
            res["canonical_smiles"] = prep.canonical_smiles
            graph, feat_warnings = predictor.encode(prep.mol)
            res["warnings"] = prep.warnings + feat_warnings
            features.append(graph)
            slots.append(len(results))
        except ToxError as e:
            res["status"], res["error"] = "error", e.to_dict()
        results.append(res)

    for start in range(0, len(features), FORWARD_BATCH):
        probs = predictor.predict(features[start:start + FORWARD_BATCH])
        for row, slot in zip(probs, slots[start:start + FORWARD_BATCH]):
            results[slot]["probabilities"] = row
    return results


def to_json_record(res: dict, tasks: list[str]) -> dict:
    out = {k: res[k] for k in ("index", "id", "input_smiles", "canonical_smiles", "status", "error", "warnings")}
    if res["probabilities"] is None:
        out["predictions"] = None
    else:
        out["predictions"] = {
            t: {"probability": round(float(p), 8), "label": int(p >= THRESHOLD)}
            for t, p in zip(tasks, res["probabilities"])
        }
    return out


def csv_header(tasks: list[str]) -> list[str]:
    head = ["index", "id", "input_smiles", "canonical_smiles", "status", "error_code", "error_message", "warnings"]
    for t in tasks:
        head += [f"{t}_prob", f"{t}_label"]
    return head


def to_csv_row(res: dict, tasks: list[str]) -> list:
    err = res["error"] or {}
    message = err.get("message", "")
    if err.get("detail"):
        message = f"{message}: {err['detail']}"
    row = [res["index"], res["id"], res["input_smiles"] or "", res["canonical_smiles"] or "",
           res["status"], err.get("code", ""), message, ";".join(res["warnings"])]
    if res["probabilities"] is None:
        row += [""] * (2 * len(tasks))
    else:
        for p in np.asarray(res["probabilities"], dtype=float):
            row += [f"{p:.8f}", int(p >= THRESHOLD)]
    return row
