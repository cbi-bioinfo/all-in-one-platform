# 자체 시험 결과서 — MTDNN Toxicity Predictor 1.0.0

## 1. 시험 환경

| 항목 | 값 |
|---|---|
| 이미지 | `cbibioinfolab/toxicity-prediction:mtdnn-1.0.0` |
| 이미지 ID | `sha256:16a334b22babdefd93f649806fc79e9f01ee0620d9471a12be4cf9847a75be88` |
| 실행 장치 | GPU |
| 네트워크 | `--network none` (모든 사례) |
| 실행 시각 | 2026-10-06T12:48:14+09:00 |
| 시험 도구 | `tests/run_tests.py` |
| 허용 오차 | 확률값 절대오차 1e-06 이내, 문자열·판정값(라벨·상태·코드·메시지·경고·HTTP 상태·종료 코드)은 완전 일치 |

**결과: 18/18 일치**

## 2. 골든 데이터셋 시험 결과 (`/tests/golden/`)

| 사례 | 구분 | 입력 요약 | 기대 결과 | 실제 결과 | 확률 최대 오차 | 일치 |
|---|---|---|---|---|---|---|
| B1 | 경계 | 요청당 최대 건수 100건 (serve) | HTTP 200, 100 ok / 0 error | HTTP 200, 100 ok / 0 error | 0.0e+00 (63100개) | 일치 |
| B2 | 경계 | 입체 표기(@) 포함 분자 vs 입체 제거 분자 — '@'는 SE 어휘에 없어 <unk>로 인코딩, 두 예측이 다름(W-ENC-001) | exit 0, 2 ok / 0 error, warn W-ENC-001 | exit 0, 2 ok / 0 error, warn W-ENC-001 | 0.0e+00 (1262개) | 일치 |
| E1 | 오류 | 고리 미종결 SMILES (serve, 단일 요청) | HTTP 422, E-INPUT-002 | HTTP 422, E-INPUT-002 | — | 일치 |
| E2 | 오류 | 전하 표기가 빠진 4급 암모늄염 raw SMILES — 원자가 오류 행만 E-INPUT-002, 나머지 계속 | exit 0, 1 ok / 1 error, E-INPUT-002, warn W-ENC-001,W-STD-001,W-STD-002 | exit 0, 1 ok / 1 error, E-INPUT-002, warn W-ENC-001,W-STD-001,W-STD-002 | 0.0e+00 (631개) | 일치 |
| N1 | 정상 | 단일 화합물 (captan, trainset 홀드아웃 test 분자) | exit 0, 1 ok / 0 error | exit 0, 1 ok / 0 error | 0.0e+00 (631개) | 일치 |
| N2 | 정상 | 10건 일괄 예측 (CSV) | exit 0, 10 ok / 0 error | exit 0, 10 ok / 0 error | 0.0e+00 (6310개) | 일치 |
| N3 | 정상 | 나트륨 염·이온화 raw SMILES (.smi 입력) — 학습과 동일하게 그대로 예측, 경고 표시 | exit 0, 1 ok / 0 error, warn W-ENC-001,W-STD-001,W-STD-002 | exit 0, 1 ok / 0 error, warn W-ENC-001,W-STD-001,W-STD-002 | 0.0e+00 (631개) | 일치 |

## 3. 보조 시험 결과 (`/tests/cases/`)

| 사례 | 구분 | 입력 요약 | 기대 결과 | 실제 결과 | 확률 최대 오차 | 일치 |
|---|---|---|---|---|---|---|
| S1 | 오류 | 요청당 최대 건수 초과 101건 (serve) | HTTP 413, E-INPUT-003 | HTTP 413, E-INPUT-003 | — | 일치 |
| S10 | 오류 | T2 작업 — smiles 열이 없는 CSV 제출, 작업 상태 failed + E-INPUT-005 | HTTP 202, job failed, E-INPUT-005 | HTTP 202, job failed, E-INPUT-005 | — | 일치 |
| S11 | 오류 | 존재하지 않는 job_id 상태 조회 — 404 E-JOB-001 | HTTP 404, E-JOB-001 | HTTP 404, E-JOB-001 | — | 일치 |
| S2 | 오류 | 빈 요청 목록 (serve) | HTTP 422, E-INPUT-006 | HTTP 422, E-INPUT-006 | — | 일치 |
| S3 | 오류 | smiles 컬럼이 없는 CSV (batch) | exit 2, E-INPUT-005 | exit 2, E-INPUT-005 | — | 일치 |
| S4 | 오류 | 지원하지 않는 입력 형식 .xlsx (batch) | exit 2, E-INPUT-004 | exit 2, E-INPUT-004 | — | 일치 |
| S5 | 경계 | 체크포인트 재시작 — CHUNK_SIZE=3, MAX_CHUNKS_PER_RUN=2로 중단 후 재실행 (N2와 동일 결과) | exit [5, 0], 10 ok / 0 error | exit [5, 0], 10 ok / 0 error | 0.0e+00 (6310개) | 일치 |
| S6 | 정상 | STANDARDIZE=1 — 염 제거·전하 중화 후 예측 (N3과 같은 입력) | exit 0, 1 ok / 0 error, warn W-STD-001,W-STD-002,W-STD-003 | exit 0, 1 ok / 0 error, warn W-STD-001,W-STD-002,W-STD-003 | 0.0e+00 (631개) | 일치 |
| S7 | 경계 | 정상·오류 혼합 요청 — 200 응답에 행별 오류 포함 (serve) | HTTP 200, 2 ok / 1 error | HTTP 200, 2 ok / 1 error | 0.0e+00 (1262개) | 일치 |
| S8 | 정상 | 전하 분리 없이 표기한 니트로기 raw SMILES — RDKit이 [N+](=O)[O-]로 자동 정규화, 올바른 표기와 동일 예측 | exit 0, 2 ok / 0 error, warn W-STD-002 | exit 0, 2 ok / 0 error, warn W-STD-002 | 0.0e+00 (1262개) | 일치 |
| S9 | 정상 | T2 작업 인터페이스 — POST /jobs 제출 → GET /jobs/{job_id} 상태 → GET /jobs/{job_id}/result 결과 (입력·기대 결과는 E2와 같음: batch와 동일 결과) | HTTP 202, job completed, 1 ok / 1 error | HTTP 202, job completed, 1 ok / 1 error | 0.0e+00 (631개) | 일치 |

## 4. 추가 검증 (재현성·정확성)

| 항목 | 방법 | 결과 |
|---|---|---|
| 반복 실행 결정성 (GPU) | seed0 test 506분자 × 631태스크를 같은 이미지로 2회 batch 실행해 비교 | 최대 절대오차 **0** (319,286개 확률값) |
| 장치 간 결정성 (GPU ↔ CPU) | 같은 입력을 `DEVICE=cuda`와 `DEVICE=cpu`로 실행해 비교 | 최대 절대오차 **0**, 라벨 불일치 0 |
| batch ↔ serve 일치 | B1(100건) serve 응답과 같은 분자의 batch 결과 비교 | 최대 절대오차 **0**, 라벨 일치 |
| batch ↔ 작업 API 일치 | E2 입력을 `POST /jobs`로 제출해 받은 결과 파일과 batch 기대 결과 비교 (S9) | 파일 바이트 단위 동일 |
| 작업 API 재시작 이어하기 | 3,000분자 작업(`CHUNK_SIZE=200`, 15청크)을 5청크 처리 후 서버 중지 → 같은 `JOBS_DIR`로 재시작 | 재시작 시 자동 재대기열, 6번째 청크부터 처리, `chunks_resumed=5`, 3,000건 완료 |
| 평가 성능 재현 | 컨테이너 예측으로 seed0 test 지표를 다시 계산해 학습 환경 평가값과 비교 | macro AUROC 0.699450 / F1 0.263334 / 민감도 0.254221 / 특이도 0.871793 — 소수점 6자리까지 일치 |
| 오프라인 실행 | 모든 시험을 `--network none`으로 실행 | 정상 동작 |
| 비루트 실행 | 이미지 `User` 설정과 출력 파일 소유자 확인 | UID 10001 (`app`) |
| 가중치 무결성 | 시작 시 `models/SHA256SUMS` 검증 | 4개 파일 일치 |
| 자원 사용량 (RTX 2080 Ti, 506분자) | `docker stats`, `nvidia-smi` 1초 간격 표본 | 최대 RAM 6.7 GiB, 최대 GPU 메모리 4.1 GB, 처리량 69–76 분자/초, 모델 로드 약 35초 |

## 5. 사례별 파일

각 사례 디렉터리에 입력 파일과 기대 결과 파일이 쌍으로 있다.

* batch 사례: `input.*` → `expected.csv` (`case.json`에 환경 변수·기대 종료 코드)
* serve 사례: `request.json` → `expected.json` (`case.json`에 기대 HTTP 상태)
* job 사례: `input.*`를 `POST /jobs`로 제출 → `GET /jobs/{job_id}` 상태가 끝날 때까지 조회 → `GET /jobs/{job_id}/result` 결과를 `expected.csv`, 최종 상태를 `expected_job.json`과 비교

재실행: `python3 tests/run_tests.py --image <이미지>` (GPU 없으면 `--cpu`).
