#!/usr/bin/env python3
"""Golden-set and supplementary self-tests for the MTDNN container.

Runs every case under tests/golden/ (required N/B/E cases) and tests/cases/
(supplementary) against a built image, with networking disabled
(`--network none`). Needs only Docker and Python 3.8+ standard library.

  python3 tests/run_tests.py --image cbibioinfolab/toxicity-prediction:mtdnn-1.0.0
  python3 tests/run_tests.py --image ... --cpu            # no GPU on this host
  python3 tests/run_tests.py --image ... --only N1 E1     # subset
  python3 tests/run_tests.py --image ... --bless          # (re)write expected files

Pass criteria: probabilities within ABS_TOL of the expected value; every other
field (ids, SMILES, labels, status, codes, messages, warnings, HTTP status,
exit code) must match exactly. Results go to tests/_runs/<timestamp>/.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

ABS_TOL = 1e-6
HERE = Path(__file__).resolve().parent
SERVE_PORT = 8000
VOLATILE_KEYS = {"started_at", "finished_at", "elapsed_sec", "throughput_mol_per_sec", "output",
                 "job_id", "submitted_at"}
JOB_TIMEOUT_SEC = 600


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


# ── comparison ────────────────────────────────────────────────────────────────

def _is_prob_key(key: str) -> bool:
    return key == "probability" or key.endswith("_prob")


def compare(expected, actual, path="$", key="", diffs=None, stats=None):
    diffs = [] if diffs is None else diffs
    stats = {"max_abs_diff": 0.0, "n_prob": 0} if stats is None else stats
    if isinstance(expected, dict) and isinstance(actual, dict):
        for k in sorted(set(expected) | set(actual)):
            if k not in actual or k not in expected:
                diffs.append(f"{path}.{k}: key missing on {'actual' if k not in actual else 'expected'} side")
            else:
                compare(expected[k], actual[k], f"{path}.{k}", k, diffs, stats)
    elif isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            diffs.append(f"{path}: length {len(actual)} != expected {len(expected)}")
        for i, (e, a) in enumerate(zip(expected, actual)):
            compare(e, a, f"{path}[{i}]", key, diffs, stats)
    elif _is_prob_key(key) and expected not in ("", None) and actual not in ("", None):
        d = abs(float(expected) - float(actual))
        stats["n_prob"] += 1
        stats["max_abs_diff"] = max(stats["max_abs_diff"], d)
        if d > ABS_TOL:
            diffs.append(f"{path}: |{actual} - {expected}| = {d:.3e} > {ABS_TOL:g}")
    elif expected != actual:
        diffs.append(f"{path}: {actual!r} != expected {expected!r}")
    return diffs, stats


def read_csv(path: Path) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


# ── runners ───────────────────────────────────────────────────────────────────

def run_batch(case_dir: Path, case: dict, args, workdir: Path) -> dict:
    out = workdir / case["id"]
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    out.chmod(0o777)
    env = {"INPUT_PATH": f"/data/input/{case['input']}", **case.get("env", {})}
    cmd = ["docker", "run", "--rm", "--network", "none", *args.gpu_args,
           "-v", f"{case_dir}:/data/input:ro", "-v", f"{out}:/data/output"]
    for k, v in env.items():
        cmd += ["-e", f"{k}={v}"]
    cmd.append(args.image)

    runs = case.get("runs", 1)  # >1: same command repeated (checkpoint/resume)
    exit_codes, logs = [], []
    for _ in range(runs):
        p = sh(cmd)
        exit_codes.append(p.returncode)
        logs.append(p.stderr)
    actual = {"exit_code": exit_codes if runs > 1 else exit_codes[0]}
    log_text = "\n".join(logs)
    if (out / "predictions.csv").is_file():
        actual["output"] = read_csv(out / "predictions.csv")
    if (out / "run_summary.json").is_file():
        summary = json.loads((out / "run_summary.json").read_text())
        actual["summary"] = {k: v for k, v in summary.items() if k not in VOLATILE_KEYS}
    actual["log_contains"] = {s: s in log_text for s in case["expect"].get("log_contains", [])}
    actual["_log"] = log_text
    return actual


class Server:
    def __init__(self, args, case_root: Path):
        self.name = f"mtdnn-selftest-{int(time.time())}"
        p = sh(["docker", "run", "-d", "--rm", "--network", "none", *args.gpu_args, "--name", self.name,
                "-v", f"{case_root}:/tests:ro", args.image, "serve"])
        if p.returncode != 0:
            raise RuntimeError(p.stderr)
        for _ in range(180):
            r = self.request("GET", "/health")
            if r and r.get("status") == 200:
                return
            time.sleep(2)
        self.stop()
        raise RuntimeError("server did not become healthy")

    def request(self, method: str, path: str, body_file: str | None = None,
                content_type: str = "application/json", raw: bool = False) -> dict | None:
        data_line = f"data=open({body_file!r},'rb').read()\n" if body_file else "data=None\n"
        body_expr = "b.decode()" if raw else "json.loads(b)"
        code = "import json,sys,urllib.request,urllib.error\n" + data_line + (
            f"req=urllib.request.Request('http://127.0.0.1:{SERVE_PORT}{path}',data=data,method={method!r},"
            f"headers={{'Content-Type':{content_type!r}}})\n"
            "try:\n r=urllib.request.urlopen(req,timeout=600); s,b=r.status,r.read()\n"
            "except urllib.error.HTTPError as e: s,b=e.code,e.read()\n"
            f"print(json.dumps({{'status':s,'body':{body_expr}}}))\n"
        )
        p = sh(["docker", "exec", self.name, "python", "-c", code])
        return json.loads(p.stdout) if p.returncode == 0 and p.stdout.strip() else None

    def stop(self):
        sh(["docker", "stop", "-t", "5", self.name])


def run_serve(case_dir: Path, case: dict, server: Server, case_root: Path) -> dict:
    rel = case_dir.relative_to(case_root)
    body = f"/tests/{rel}/{case['request']}" if "request" in case else None
    r = server.request(case.get("method", "POST"), case.get("path", "/predict"), body)
    if r is None:
        return {"http_status": None, "body": None}
    return {"http_status": r["status"], "body": r["body"]}


def run_job(case_dir: Path, case: dict, server: Server, case_root: Path) -> dict:
    """T2 job API: POST /jobs -> poll GET /jobs/{id} -> GET /jobs/{id}/result."""
    rel = case_dir.relative_to(case_root)
    fmt = Path(case["input"]).suffix.lstrip(".")
    r = server.request("POST", f"/jobs?input_format={fmt}&output_format=csv", f"/tests/{rel}/{case['input']}",
                       content_type=case.get("content_type", "application/octet-stream"))
    if r is None:
        return {"http_status": None}
    actual = {"http_status": r["status"]}
    if r["status"] != 202:
        actual["body"] = r["body"]
        return actual
    job_id = r["body"]["job_id"]
    deadline = time.time() + JOB_TIMEOUT_SEC
    status = r["body"]
    while status["state"] in ("queued", "running") and time.time() < deadline:
        time.sleep(1)
        status = server.request("GET", f"/jobs/{job_id}")["body"]
    summary = status.get("summary") or {}
    actual["job"] = {**{k: v for k, v in status.items() if k not in VOLATILE_KEYS | {"summary"}},
                     "summary": {k: v for k, v in summary.items() if k not in VOLATILE_KEYS | {"device"}} or None}
    if status["state"] == "completed":
        res = server.request("GET", f"/jobs/{job_id}/result", raw=True)
        actual["output"] = list(csv.DictReader(res["body"].splitlines()))
    return actual


# ── expectations ──────────────────────────────────────────────────────────────

def check(case_dir: Path, case: dict, actual: dict, bless: bool) -> tuple[list[str], dict]:
    exp = case["expect"]
    diffs, stats = [], {"max_abs_diff": 0.0, "n_prob": 0}
    for key in ("exit_code", "http_status"):
        if key in exp and exp[key] != actual.get(key):
            diffs.append(f"{key}: {actual.get(key)} != expected {exp[key]}")
    for s, found in actual.get("log_contains", {}).items():
        if not found:
            diffs.append(f"log does not contain {s!r}")
    for key, loader in (("output", read_csv), ("body", lambda p: json.loads(p.read_text())),
                        ("summary", lambda p: json.loads(p.read_text())), ("job", lambda p: json.loads(p.read_text()))):
        if key not in exp:
            continue
        path = case_dir / exp[key]
        if bless and actual.get(key) is not None:
            if key == "output":
                src = actual[key]
                with open(path, "w", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=list(src[0].keys()) if src else [])
                    w.writeheader()
                    w.writerows(src)
            else:
                path.write_text(json.dumps(actual[key], indent=2, ensure_ascii=False) + "\n")
        if not path.is_file():
            diffs.append(f"expected file {path.name} missing")
            continue
        d, st = compare(loader(path), actual.get(key))
        diffs += d
        stats["n_prob"] += st["n_prob"]
        stats["max_abs_diff"] = max(stats["max_abs_diff"], st["max_abs_diff"])
    return diffs, stats


def summarize_actual(case: dict, actual: dict) -> str:
    if "job" in actual:
        job, rows = actual["job"], actual.get("output") or []
        parts = [f"HTTP {actual['http_status']}, job {job['state']}"]
        if rows:
            parts.append(f"{sum(r['status'] == 'ok' for r in rows)} ok / {sum(r['status'] == 'error' for r in rows)} error")
        if job.get("error"):
            parts.append(job["error"]["code"])
        return ", ".join(parts)
    if "http_status" in actual:
        b = actual.get("body") or {}
        if "error" in b:
            return f"HTTP {actual['http_status']}, {b['error']['code']}"
        return f"HTTP {actual['http_status']}, {b.get('n_ok')} ok / {b.get('n_error')} error"
    rows = actual.get("output") or []
    codes = sorted({r["error_code"] for r in rows if r.get("error_code")})
    warns = sorted({w for r in rows for w in (r.get("warnings") or "").split(";") if w})
    parts = [f"exit {actual['exit_code']}"]
    if rows:
        parts.append(f"{sum(r['status'] == 'ok' for r in rows)} ok / {sum(r['status'] == 'error' for r in rows)} error")
    if codes:
        parts.append(",".join(codes))
    if warns:
        parts.append("warn " + ",".join(warns))
    parts += [s for s, found in actual.get("log_contains", {}).items() if found and s.startswith("E-")]
    return ", ".join(parts)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--image", required=True)
    ap.add_argument("--cpu", action="store_true", help="run without --gpus (CPU inference)")
    ap.add_argument("--only", nargs="*", help="case ids to run")
    ap.add_argument("--bless", action="store_true", help="write current outputs as expected files")
    ap.add_argument("--suites", nargs="*", default=["golden", "cases"])
    args = ap.parse_args()
    args.gpu_args = [] if args.cpu else ["--gpus", "all"]

    cases = []
    for suite in args.suites:
        for d in sorted((HERE / suite).iterdir()):
            if (d / "case.json").is_file():
                c = json.loads((d / "case.json").read_text())
                if not args.only or c["id"] in args.only:
                    cases.append((suite, d, c))

    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    run_dir = HERE / "_runs" / stamp
    run_dir.mkdir(parents=True)
    image_id = sh(["docker", "image", "inspect", "--format", "{{.Id}}", args.image]).stdout.strip()

    server = None
    if any(c["mode"] in ("serve", "job") for _, _, c in cases):
        print("starting serve-mode container ...", flush=True)
        server = Server(args, HERE)
    results = []
    try:
        with tempfile.TemporaryDirectory(dir=run_dir) as tmp:
            for suite, d, c in cases:
                t0 = time.time()
                if c["mode"] == "serve":
                    actual = run_serve(d, c, server, HERE)
                elif c["mode"] == "job":
                    actual = run_job(d, c, server, HERE)
                else:
                    actual = run_batch(d, c, args, Path(tmp))
                diffs, stats = check(d, c, actual, args.bless)
                ok = not diffs
                results.append({
                    "suite": suite, "id": c["id"], "category": c["category"], "title": c["title"],
                    "mode": c["mode"], "pass": ok, "diffs": diffs[:20], "n_diffs": len(diffs),
                    "max_abs_prob_diff": stats["max_abs_diff"], "n_prob_compared": stats["n_prob"],
                    "actual_summary": summarize_actual(c, actual), "seconds": round(time.time() - t0, 1),
                })
                if c["mode"] == "batch":
                    (run_dir / f"{c['id']}.log").write_text(actual.get("_log", ""))
                print(f"[{'PASS' if ok else 'FAIL'}] {c['id']:4s} {c['title']}  ({results[-1]['actual_summary']})", flush=True)
                for line in diffs[:5]:
                    print(f"       {line}", flush=True)
    finally:
        if server:
            server.stop()

    report = {"image": args.image, "image_id": image_id, "device": "cpu" if args.cpu else "gpu",
              "abs_tol": ABS_TOL, "run_at": datetime.now().astimezone().isoformat(timespec="seconds"), "n_pass": sum(r["pass"] for r in results),
              "n_total": len(results), "results": results}
    (run_dir / "results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\n{report['n_pass']}/{report['n_total']} passed — {run_dir / 'results.json'}")
    return 0 if report["n_pass"] == report["n_total"] else 1


if __name__ == "__main__":
    sys.exit(main())
