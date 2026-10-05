#!/usr/bin/env python3
"""Render docs/selftest_report.md from a tests/_runs/<stamp>/results.json.

  python3 tests/make_report.py                      # latest run
  python3 tests/make_report.py tests/_runs/<stamp>/results.json
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CATEGORY = {"normal": "정상", "boundary": "경계", "error": "오류"}


def expected_summary(case_dir: Path, case: dict) -> str:
    exp = case["expect"]
    if "http_status" in exp:
        body = json.loads((case_dir / exp["body"]).read_text()) if "body" in exp else {}
        if "error" in body:
            return f"HTTP {exp['http_status']}, {body['error']['code']}"
        return f"HTTP {exp['http_status']}, {body.get('n_ok')} ok / {body.get('n_error')} error"
    parts = [f"exit {exp['exit_code']}"]
    if "output" in exp:
        import csv
        rows = list(csv.DictReader(open(case_dir / exp["output"], newline="")))
        parts.append(f"{sum(r['status'] == 'ok' for r in rows)} ok / {sum(r['status'] == 'error' for r in rows)} error")
        codes = sorted({r["error_code"] for r in rows if r["error_code"]})
        warns = sorted({w for r in rows for w in r["warnings"].split(";") if w})
        if codes:
            parts.append(",".join(codes))
        if warns:
            parts.append("warn " + ",".join(warns))
    for s in exp.get("log_contains", []):
        if s.startswith("E-"):
            parts.append(s)
    return ", ".join(parts)


def main():
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        path = sorted((HERE / "_runs").glob("*/results.json"))[-1]
    rep = json.loads(path.read_text())
    lines = [
        "# 자체 시험 결과서 — ToxKG-GPS Toxicity Predictor 1.0.0",
        "",
        "## 1. 시험 환경",
        "",
        "| 항목 | 값 |",
        "|---|---|",
        f"| 이미지 | `{rep['image']}` |",
        f"| 이미지 ID | `{rep['image_id']}` |",
        f"| 실행 장치 | {rep['device'].upper()} |",
        "| 네트워크 | `--network none` (모든 사례) |",
        f"| 실행 시각 | {rep['run_at']} |",
        "| 시험 도구 | `tests/run_tests.py` |",
        f"| 허용 오차 | 확률값 절대오차 {rep['abs_tol']:.0e} 이내, 문자열·판정값(라벨·상태·코드·메시지·경고·HTTP 상태·종료 코드)은 완전 일치 |",
        "",
        f"**결과: {rep['n_pass']}/{rep['n_total']} 일치**",
        "",
    ]
    for suite, title in (("golden", "2. 골든 데이터셋 시험 결과 (`/tests/golden/`)"),
                         ("cases", "3. 보조 시험 결과 (`/tests/cases/`)")):
        rows = [r for r in rep["results"] if r["suite"] == suite]
        if not rows:
            continue
        lines += [f"## {title}", "",
                  "| 사례 | 구분 | 입력 요약 | 기대 결과 | 실제 결과 | 확률 최대 오차 | 일치 |",
                  "|---|---|---|---|---|---|---|"]
        for r in rows:
            case_dir = HERE / suite / r["id"]
            case = json.loads((case_dir / "case.json").read_text())
            diff = f"{r['max_abs_prob_diff']:.1e} ({r['n_prob_compared']}개)" if r["n_prob_compared"] else "—"
            lines.append(f"| {r['id']} | {CATEGORY[r['category']]} | {r['title']} | "
                         f"{expected_summary(case_dir, case)} | {r['actual_summary']} | {diff} | "
                         f"{'일치' if r['pass'] else '불일치'} |")
        lines.append("")
    fails = [r for r in rep["results"] if not r["pass"]]
    if fails:
        lines += ["## 불일치 상세", ""]
        for r in fails:
            lines.append(f"* **{r['id']}**: " + "; ".join(r["diffs"][:5]))
        lines.append("")
    extra = HERE / "extra_verification.md"
    if extra.is_file():
        lines += [extra.read_text().rstrip(), ""]
    lines += [
        "## 5. 사례별 파일",
        "",
        "각 사례 디렉터리에 입력 파일과 기대 결과 파일이 쌍으로 있다.",
        "",
        "* batch 사례: `input.*` → `expected.csv` (`case.json`에 환경 변수·기대 종료 코드)",
        "* serve 사례: `request.json` → `expected.json` (`case.json`에 기대 HTTP 상태)",
        "",
        "재실행: `python3 tests/run_tests.py --image <이미지>` (GPU 없으면 `--cpu`).",
        "",
    ]
    out = ROOT / "docs" / "selftest_report.md"
    out.write_text("\n".join(lines))
    print(f"wrote {out} from {path}")


if __name__ == "__main__":
    main()
