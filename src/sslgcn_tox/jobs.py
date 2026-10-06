"""T2 job API for serve mode: submit -> status -> result.

Each job is one batch run (batch.run) over an uploaded input file, executed
by a single background worker that reuses the already-loaded model. Jobs run
one at a time in submission order.

JOBS_DIR/<job_id>/
    job.json      state, progress, timestamps, error, run summary
    input.<ext>   uploaded input (csv, smi, txt, sdf or mol)
    output/       predictions.<csv|json>, run_summary.json, .checkpoint/

job.json is rewritten atomically on every state change and progress step, so
GET /jobs/{job_id} works across restarts. Jobs that were queued or running
when the server stopped are queued again at start-up and resume from their
chunk checkpoints.
"""
import dataclasses
import json
import logging
import os
import queue
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import batch
from .errors import ToxError

log = logging.getLogger("sslgcn_tox")

INPUT_FORMATS = ("csv", "txt", "sdf", "mol")
OUTPUT_FORMATS = ("csv", "json")
_JOB_ID = re.compile(r"^[0-9a-f]{32}$")


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class JobManager:
    def __init__(self, cfg, get_predictor):
        self.cfg = cfg
        self.get_predictor = get_predictor
        self.root = Path(cfg.jobs_dir)
        self.queue: queue.Queue[str] = queue.Queue()
        self.lock = threading.Lock()
        self.worker: threading.Thread | None = None

    # ── persistence ───────────────────────────────────────────────────────────

    def _job_dir(self, job_id: str) -> Path:
        if not _JOB_ID.match(job_id):
            raise ToxError("E-JOB-001", job_id)
        return self.root / job_id

    def _write(self, job: dict):
        path = self._job_dir(job["job_id"]) / "job.json"
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(job, indent=2))
        os.replace(tmp, path)

    def _update(self, job_id: str, **fields) -> dict:
        with self.lock:
            job = self.get(job_id)
            job.update(fields)
            self._write(job)
            return job

    def get(self, job_id: str) -> dict:
        path = self._job_dir(job_id) / "job.json"
        if not path.is_file():
            raise ToxError("E-JOB-001", job_id)
        return json.loads(path.read_text())

    # ── API operations ────────────────────────────────────────────────────────

    def submit(self, data: bytes, input_format: str, output_format: str) -> dict:
        if input_format not in INPUT_FORMATS:
            raise ToxError("E-INPUT-004", f"input_format={input_format!r} (use {', '.join(INPUT_FORMATS)})")
        if output_format not in OUTPUT_FORMATS:
            raise ToxError("E-INPUT-011", f"output_format={output_format!r} (use csv or json)")
        if not data.strip():
            raise ToxError("E-INPUT-006", "empty request body")
        job_id = uuid.uuid4().hex
        job_dir = self.root / job_id
        try:
            job_dir.mkdir(parents=True)
            (job_dir / f"input.{input_format}").write_bytes(data)
        except OSError as e:
            raise ToxError("E-SYS-001", f"{self.root}: {e.strerror}")
        job = {
            "job_id": job_id, "state": "queued",
            "input_format": input_format, "output_format": output_format,
            "submitted_at": _now(), "started_at": None, "finished_at": None, "elapsed_sec": None,
            "n_total": None, "n_processed": 0, "progress_percent": 0.0,
            "chunks": None, "chunks_completed": 0,
            "error": None, "summary": None,
        }
        with self.lock:
            self._write(job)
        self.queue.put(job_id)
        log.info("Job %s queued (%s, %d bytes)", job_id, input_format, len(data))
        return job

    def result_path(self, job_id: str) -> tuple[Path, str]:
        job = self.get(job_id)
        if job["state"] != "completed":
            raise ToxError("E-JOB-002", f"state={job['state']}")
        fmt = job["output_format"]
        return self._job_dir(job_id) / "output" / f"predictions.{fmt}", fmt

    # ── worker ────────────────────────────────────────────────────────────────

    def start(self):
        """Re-queue unfinished jobs from a previous server run, then start the worker."""
        self.root.mkdir(parents=True, exist_ok=True)
        pending = []
        for path in self.root.glob("*/job.json"):
            try:
                job = json.loads(path.read_text())
            except (OSError, ValueError):
                continue
            if job.get("state") in ("queued", "running"):
                pending.append((job["submitted_at"], job["job_id"]))
        for _, job_id in sorted(pending):
            self._update(job_id, state="queued")
            self.queue.put(job_id)
        if pending:
            log.info("Re-queued %d unfinished job(s) from %s", len(pending), self.root)
        self.worker = threading.Thread(target=self._loop, name="job-worker", daemon=True)
        self.worker.start()

    def _loop(self):
        while True:
            self._run(self.queue.get())

    def _run(self, job_id: str):
        job = self.get(job_id)
        job_dir = self._job_dir(job_id)
        out = job_dir / "output"
        cfg = dataclasses.replace(
            self.cfg, input_path=job_dir / f"input.{job['input_format']}", output_dir=out,
            checkpoint_dir=out / ".checkpoint", output_format=job["output_format"],
            resume=True, max_chunks_per_run=0,
        )
        t0 = time.time()
        self._update(job_id, state="running", started_at=job["started_at"] or _now())

        def progress(processed, total, chunks_done, n_chunks):
            self._update(job_id, n_total=total, n_processed=processed,
                         progress_percent=round(100 * processed / total, 1),
                         chunks=n_chunks, chunks_completed=chunks_done)

        log.info("Job %s started", job_id)
        try:
            batch.run(cfg, predictor=self.get_predictor(), on_progress=progress)
            summary = json.loads((out / "run_summary.json").read_text())
            self._update(job_id, state="completed", finished_at=_now(),
                         elapsed_sec=round(time.time() - t0, 2), summary=summary)
            log.info("Job %s completed", job_id)
        except ToxError as e:
            self._update(job_id, state="failed", finished_at=_now(),
                         elapsed_sec=round(time.time() - t0, 2), error=e.to_dict())
            log.error("Job %s failed: %s", job_id, e)
        except Exception as e:
            log.exception("Job %s failed: E-SYS-003", job_id)
            self._update(job_id, state="failed", finished_at=_now(), elapsed_sec=round(time.time() - t0, 2),
                         error=ToxError("E-SYS-003", f"{type(e).__name__}: {e}").to_dict())
