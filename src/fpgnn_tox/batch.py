"""T2 batch mode: process INPUT_PATH in chunks, then exit.

* Progress log  — one line per chunk: done/total, %, elapsed, ETA, rate.
* Checkpoints   — each finished chunk is written atomically to CHECKPOINT_DIR
                  together with progress.json. Re-running the same command
                  skips finished chunks (RESUME=1, default).
* Run time      — start/end time and elapsed seconds go to the log and to
                  OUTPUT_DIR/run_summary.json.
* Time-boxing   — MAX_CHUNKS_PER_RUN=N stops after N new chunks with exit
                  code 5 (status "partial"); run again to continue.

The serve-mode job API (jobs.py) runs the same function per job, passing the
already-loaded predictor and a progress callback.
"""
import csv
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from . import TOOL_ID, __version__
from .engine import Predictor
from .errors import ToxError
from .inputs import read_input
from .service import csv_header, run_records, to_csv_row, to_json_record

log = logging.getLogger("fpgnn_tox")


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _hms(sec: float) -> str:
    sec = int(sec)
    return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _atomic_write(path: Path, text: str):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def run(cfg, predictor=None, on_progress=None) -> int:
    if cfg.input_path is None:
        raise ToxError("E-INPUT-001", "INPUT_PATH is not set")
    if cfg.output_format not in ("csv", "json"):
        raise ToxError("E-SYS-004", f"OUTPUT_FORMAT={cfg.output_format!r} (use csv or json)")
    if cfg.chunk_size < 1:
        raise ToxError("E-SYS-004", f"CHUNK_SIZE={cfg.chunk_size}")
    try:
        cfg.output_dir.mkdir(parents=True, exist_ok=True)
        cfg.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        probe = cfg.output_dir / ".write_test"
        probe.write_text("")
        probe.unlink()
    except OSError as e:
        raise ToxError("E-SYS-001", f"{cfg.output_dir}: {e.strerror}")

    started, t0 = _now(), time.time()
    log.info("%s %s — batch run started at %s", TOOL_ID, __version__, started)
    records = read_input(cfg.input_path)
    total = len(records)
    chunks = [records[i:i + cfg.chunk_size] for i in range(0, total, cfg.chunk_size)]
    log.info("Input: %s — %d molecules in %d chunk(s) of %d", cfg.input_path, total, len(chunks), cfg.chunk_size)

    predictor = predictor or Predictor(cfg)
    run_key = {
        "input_sha256": _file_sha256(cfg.input_path), "chunk_size": cfg.chunk_size,
        "standardize": cfg.standardize, "max_smiles_length": cfg.max_smiles_length,
        "model_sha256": predictor.model_sha256, "version": __version__,
    }
    progress_file = cfg.checkpoint_dir / "progress.json"
    done: set[int] = set()
    if cfg.resume and progress_file.is_file():
        prev = json.loads(progress_file.read_text())
        if prev.get("run_key") == run_key:
            done = {i for i in prev.get("completed_chunks", [])
                    if (cfg.checkpoint_dir / f"chunk_{i:05d}.json").is_file()}
            log.info("Resuming: %d/%d chunk(s) already finished", len(done), len(chunks))
        else:
            log.warning("Checkpoint in %s belongs to a different input/config — starting fresh", cfg.checkpoint_dir)
    if not done:
        for old in cfg.checkpoint_dir.glob("chunk_*.json"):
            old.unlink()
    resumed = len(done)

    processed = sum(len(chunks[i]) for i in done)
    if on_progress:
        on_progress(processed, total, len(done), len(chunks))
    new_done, new_chunks, t_work = 0, 0, time.time()
    for i, chunk in enumerate(chunks):
        if i in done:
            continue
        if cfg.max_chunks_per_run and new_chunks >= cfg.max_chunks_per_run:
            elapsed = time.time() - t0
            _atomic_write(cfg.output_dir / "run_summary.json", json.dumps({
                "tool_id": TOOL_ID, "version": __version__, "status": "partial",
                "started_at": started, "finished_at": _now(), "elapsed_sec": round(elapsed, 2),
                "n_total": total, "n_processed": processed, "chunks": len(chunks),
                "chunks_completed": len(done), "checkpoint_dir": str(cfg.checkpoint_dir),
            }, indent=2))
            log.info("Stopped after MAX_CHUNKS_PER_RUN=%d — %d/%d chunk(s) done, elapsed %s; "
                     "run the same command again to resume", cfg.max_chunks_per_run, len(done), len(chunks), _hms(elapsed))
            return 5
        results = [to_json_record(r, predictor.tasks) for r in run_records(predictor, chunk, cfg)]
        _atomic_write(cfg.checkpoint_dir / f"chunk_{i:05d}.json", json.dumps(results))
        done.add(i)
        _atomic_write(progress_file, json.dumps({"run_key": run_key, "completed_chunks": sorted(done),
                                                 "updated_at": _now()}))
        processed += len(chunk)
        new_done += len(chunk)
        new_chunks += 1
        rate = new_done / max(time.time() - t_work, 1e-9)
        eta = (total - processed) / rate if rate > 0 else 0
        log.info("[progress] %d/%d (%.1f%%) chunk %d/%d elapsed=%s eta=%s rate=%.1f mol/s",
                 processed, total, 100 * processed / total, i + 1, len(chunks),
                 _hms(time.time() - t0), _hms(eta), rate)
        if on_progress:
            on_progress(processed, total, len(done), len(chunks))

    # merge chunks -> final output
    out_path = cfg.output_dir / f"predictions.{cfg.output_format}"
    n_ok = n_err = n_warn = 0
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    with open(tmp, "w", newline="") as f:
        writer = csv.writer(f) if cfg.output_format == "csv" else None
        if writer:
            writer.writerow(csv_header(predictor.tasks))
        else:
            f.write("[\n")
        first = True
        for i in range(len(chunks)):
            for rec in json.loads((cfg.checkpoint_dir / f"chunk_{i:05d}.json").read_text()):
                n_ok += rec["status"] == "ok"
                n_err += rec["status"] == "error"
                n_warn += bool(rec["warnings"])
                if writer:
                    probs = None if rec["predictions"] is None else [v["probability"] for v in rec["predictions"].values()]
                    writer.writerow(to_csv_row({**rec, "probabilities": probs}, predictor.tasks))
                else:
                    f.write(("" if first else ",\n") + json.dumps(rec))
                    first = False
        if not writer:
            f.write("\n]\n")
    os.replace(tmp, out_path)

    finished, elapsed = _now(), time.time() - t0
    summary = {
        "tool_id": TOOL_ID, "version": __version__, "status": "completed",
        "started_at": started, "finished_at": finished, "elapsed_sec": round(elapsed, 2),
        "n_total": total, "n_ok": n_ok, "n_error": n_err, "n_with_warnings": n_warn,
        "chunks": len(chunks), "chunks_resumed": resumed,
        "throughput_mol_per_sec": round(new_done / max(time.time() - t_work, 1e-9), 2) if new_done else None,
        "device": str(predictor.device), "seed": cfg.seed, "standardize": cfg.standardize,
        "model_sha256": predictor.model_sha256, "n_tasks": len(predictor.tasks),
        "output": str(out_path),
    }
    _atomic_write(cfg.output_dir / "run_summary.json", json.dumps(summary, indent=2))
    for f in [progress_file, *cfg.checkpoint_dir.glob("chunk_*.json")]:
        f.unlink(missing_ok=True)
    try:
        cfg.checkpoint_dir.rmdir()  # only if now empty
    except OSError:
        pass
    log.info("Finished at %s — elapsed %s; %d ok, %d error(s); output: %s",
             finished, _hms(elapsed), n_ok, n_err, out_path)
    return 0
