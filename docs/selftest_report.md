# 자체 시험 결과서 — GROVER Toxicity Predictor 1.0.0

## 1. 시험 환경

| 항목 | 값 |
|---|---|
| 이미지 | `pzkeung/bio-synergy-platform:grover-1.0.0` |
| 이미지 ID | `sha256:2ea4340cc150bdda550a580eff5c20d5a4798699dcdce1f31b1525b98151b769` |
| 실행 장치 | GPU |
| 네트워크 | `--network none` (모든 사례) |
| 실행 시각 | 2026-10-06T10:09:09+09:00 |
| 시험 도구 | `tests/run_tests.py` |
| 허용 오차 | 확률값 절대오차 1e-06 이내, 문자열·판정값(라벨·상태·코드·메시지·경고·HTTP 상태·종료 코드)은 완전 일치 |

**결과: 20/20 일치**

## 2. 골든 데이터셋 시험 결과 (`/tests/golden/`)

| 사례 | 구분 | 입력 요약 | 기대 결과 | 실제 결과 | 확률 최대 오차 | 일치 |
|---|---|---|---|---|---|---|
| B1 | 경계 | 요청당 최대 건수 100건 (serve) | HTTP 200, 100 ok / 0 error | HTTP 200, 100 ok / 0 error | 0.0e+00 (63100개) | 일치 |
| B2 | 경계 | 입체 표기 [C@@H] / 반대 입체 [C@H] / 입체 제거 — GROVER는 키랄 태그를 특징으로 써 세 예측이 모두 다름 | exit 0, 3 ok / 0 error | exit 0, 3 ok / 0 error | 0.0e+00 (1893개) | 일치 |
| E1 | 오류 | 고리 미종결 SMILES (serve, 단일 요청) | HTTP 422, E-INPUT-002 | HTTP 422, E-INPUT-002 | — | 일치 |
| E2 | 오류 | 전하 표기가 빠진 4급 암모늄염 raw SMILES — 원자가 오류 행만 E-INPUT-002, 나머지 계속 | exit 0, 1 ok / 1 error, E-INPUT-002, warn W-STD-001,W-STD-002 | exit 0, 1 ok / 1 error, E-INPUT-002, warn W-STD-001,W-STD-002 | 0.0e+00 (631개) | 일치 |
| N1 | 정상 | 단일 화합물 (atrazine, trainset 홀드아웃 seed2 test 분자) | exit 0, 1 ok / 0 error | exit 0, 1 ok / 0 error | 0.0e+00 (631개) | 일치 |
| N2 | 정상 | 10건 일괄 예측 (CSV, seed2 test 분자) | exit 0, 10 ok / 0 error | exit 0, 10 ok / 0 error | 0.0e+00 (6310개) | 일치 |
| N3 | 정상 | 나트륨 염·이온화 raw SMILES (.smi 입력) — 학습과 같이 염 포함 그대로 예측, W-STD 경고 | exit 0, 1 ok / 0 error, warn W-STD-001,W-STD-002 | exit 0, 1 ok / 0 error, warn W-STD-001,W-STD-002 | 0.0e+00 (631개) | 일치 |

## 3. 보조 시험 결과 (`/tests/cases/`)

| 사례 | 구분 | 입력 요약 | 기대 결과 | 실제 결과 | 확률 최대 오차 | 일치 |
|---|---|---|---|---|---|---|
| S1 | 오류 | 요청당 최대 건수 초과 101건 (serve) | HTTP 413, E-INPUT-003 | HTTP 413, E-INPUT-003 | — | 일치 |
| S10 | 경계 | 배위결합(->) 표기 — 단일·이중·삼중·방향족 밖 결합은 결합 유형 특징이 0이 되어 W-FEAT-001 | exit 0, 2 ok / 0 error, warn W-FEAT-001 | exit 0, 2 ok / 0 error, warn W-FEAT-001 | 0.0e+00 (1262개) | 일치 |
| S11 | 경계 | 결합이 없는 무기염 KI (trainset 분자) — 간선 없는 그래프도 예측 | exit 0, 1 ok / 0 error, warn W-STD-001,W-STD-002 | exit 0, 1 ok / 0 error, warn W-STD-001,W-STD-002 | 0.0e+00 (631개) | 일치 |
| S12 | 오류 | GROVER 특징 범위 — 형식 전하 +6은 E-INPUT-013, +5·원자번호>100은 W-FEAT-002, 수소뿐인 분자는 E-INPUT-012 | exit 0, 2 ok / 2 error, E-INPUT-012,E-INPUT-013, warn W-FEAT-002,W-STD-002 | exit 0, 2 ok / 2 error, E-INPUT-012,E-INPUT-013, warn W-FEAT-002,W-STD-002 | 0.0e+00 (1262개) | 일치 |
| S13 | 경계 | 배치 독립성 — 원자 차수 6 분자(PF6 염)와 같은 파일로 예측해도 atrazine 확률은 N1과 동일 | exit 0, 2 ok / 0 error, warn W-STD-001,W-STD-002 | exit 0, 2 ok / 0 error, warn W-STD-001,W-STD-002 | 0.0e+00 (1262개) | 일치 |
| S2 | 오류 | 빈 요청 목록 (serve) | HTTP 422, E-INPUT-006 | HTTP 422, E-INPUT-006 | — | 일치 |
| S3 | 오류 | smiles 컬럼이 없는 CSV (batch) | exit 2, E-INPUT-005 | exit 2, E-INPUT-005 | — | 일치 |
| S4 | 오류 | 지원하지 않는 입력 형식 .xlsx (batch) | exit 2, E-INPUT-004 | exit 2, E-INPUT-004 | — | 일치 |
| S5 | 경계 | 체크포인트 재시작 — CHUNK_SIZE=3, MAX_CHUNKS_PER_RUN=2로 중단 후 재실행 (N2와 동일 결과) | exit [5, 0], 10 ok / 0 error | exit [5, 0], 10 ok / 0 error | 0.0e+00 (6310개) | 일치 |
| S6 | 정상 | STANDARDIZE=1 — 염 제거·전하 중화 후 예측 (N3과 같은 입력) | exit 0, 1 ok / 0 error, warn W-STD-001,W-STD-002,W-STD-003 | exit 0, 1 ok / 0 error, warn W-STD-001,W-STD-002,W-STD-003 | 0.0e+00 (631개) | 일치 |
| S7 | 경계 | 정상·오류 혼합 요청 — 200 응답에 행별 오류 포함 (serve) | HTTP 200, 1 ok / 2 error | HTTP 200, 1 ok / 2 error | 0.0e+00 (631개) | 일치 |
| S8 | 정상 | 전하 분리 없이 표기한 니트로기 raw SMILES — RDKit이 [N+](=O)[O-]로 자동 정규화, 올바른 표기와 동일 예측 | exit 0, 2 ok / 0 error, warn W-STD-002 | exit 0, 2 ok / 0 error, warn W-STD-002 | 0.0e+00 (1262개) | 일치 |
| S9 | 경계 | RDKit 버전 의존 구조 — [AlH3] 알루미늄 착물(seed2 test 분자, RDKit 2026.3.6에서 원자가 초과)은 E-INPUT-002, 나머지 행은 계속 | exit 0, 1 ok / 1 error, E-INPUT-002 | exit 0, 1 ok / 1 error, E-INPUT-002 | 0.0e+00 (631개) | 일치 |

## 4. 추가 검증 (재현성·정확성)

| 항목 | 방법 | 결과 |
|---|---|---|
| 배치 독립성 | seed2 test 1,102분자를 한 번에 vs 한 분자씩, 순서 섞기 | 최대 절대오차 4.4×10⁻¹⁶ (원본 GROVER는 배치 크기 1 vs 32에서 최대 0.335) |
| 반복 실행 결정성 (GPU) | seed2 test 입력을 RTX 2080 Ti, GTX 1080 Ti에서 각각 batch 실행 | 최대 절대오차 **0** (695,362개 확률값), 다른 열 모두 일치 |
| 장치 간 결정성 | 같은 입력을 `DEVICE=cpu`로 실행 | 최대 절대오차 **0**, 모든 열 일치 |
| batch ↔ serve | B1(100건) serve 응답 vs batch 결과 | 최대 절대오차 0 |
| 학습 환경 방식과의 비교 | 크기 32·파일 순서·float32 재채점(학습 이미지)과 분자별 비교 | 1,006분자 5.7×10⁻⁷ 이내. 학습 환경에서 차수 5–6 분자와 같은 배치였던 96분자 최대 0.305 |
| 성능 | 컨테이너 출력으로 seed2 test 채점 | AUROC 0.6411 / F1 0.0992 / 민감도 0.1013 / 특이도 0.9119 (학습 환경 방식 0.6360 / 0.0980 / 0.0999 / 0.9124), 평가 태스크 620 동일 |
| 오프라인·비루트 | 모든 시험 `--network none`, 이미지 사용자 | 정상 동작, UID 10001 |
| 가중치 무결성 | 시작 시 `SHA256SUMS` 검증 | 일치 |
| 자원 사용량 | trainset 10,974분자, RTX 2080 Ti, 1초 간격 표본 131개 | 최대 RAM 0.94 GiB, 최대 GPU 메모리 4.0 GB(장치 0 전체, 시작 전 1 MiB), 35 분자/초, 총 5분 34초 |
| CPU 처리량 | seed2 test 1,104분자 `DEVICE=cpu` | 1.7 분자/초 (10분 49초) |

측정 당시 다른 작업도 같은 서버의 GPU를 사용했으므로 처리량은 참고값이다.

## 5. 사례별 파일

각 사례 디렉터리에 입력 파일과 기대 결과 파일이 쌍으로 있다.

* batch 사례: `input.*` → `expected.csv` (`case.json`에 환경 변수·기대 종료 코드)
* serve 사례: `request.json` → `expected.json` (`case.json`에 기대 HTTP 상태)

재실행: `python3 tests/run_tests.py --image <이미지>` (GPU 없으면 `--cpu`).
