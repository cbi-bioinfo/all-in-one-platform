# 자체 시험 결과서 — SSL-GCN Toxicity Predictor 1.0.0

## 1. 시험 환경

| 항목 | 값 |
|---|---|
| 이미지 | `pzkeung/bio-synergy-platform:ssl-gcn-1.0.0` |
| 이미지 ID | `sha256:3a53d2ab60f9bfae0ea9a91c303825d3755c78258fc1f2dfc83a95a0d6652c33` |
| 실행 장치 | GPU |
| 네트워크 | `--network none` (모든 사례) |
| 실행 시각 | 2026-10-06T04:18:35+09:00 |
| 시험 도구 | `tests/run_tests.py` |
| 허용 오차 | 확률값 절대오차 1e-06 이내, 문자열·판정값(라벨·상태·코드·메시지·경고·HTTP 상태·종료 코드)은 완전 일치 |

**결과: 16/16 일치**

## 2. 골든 데이터셋 시험 결과 (`/tests/golden/`)

| 사례 | 구분 | 입력 요약 | 기대 결과 | 실제 결과 | 확률 최대 오차 | 일치 |
|---|---|---|---|---|---|---|
| B1 | 경계 | 요청당 최대 건수 100건 (serve) | HTTP 200, 100 ok / 0 error | HTTP 200, 100 ok / 0 error | 0.0e+00 (60100개) | 일치 |
| B2 | 경계 | 입체 표기 [C@H] 포함 vs 제거 분자 — 키랄성은 특징에 없지만 대괄호 원자는 암묵 원자가 0으로 인코딩되어 두 예측이 다름 | exit 0, 2 ok / 0 error | exit 0, 2 ok / 0 error | 0.0e+00 (1202개) | 일치 |
| E1 | 오류 | 고리 미종결 SMILES (serve, 단일 요청) | HTTP 422, E-INPUT-002 | HTTP 422, E-INPUT-002 | — | 일치 |
| E2 | 오류 | 전하 표기가 빠진 4급 암모늄염 raw SMILES — 원자가 오류 행만 E-INPUT-002, 나머지 계속 | exit 0, 1 ok / 1 error, E-INPUT-002, warn W-STD-001,W-STD-002 | exit 0, 1 ok / 1 error, E-INPUT-002, warn W-STD-001,W-STD-002 | 0.0e+00 (601개) | 일치 |
| N1 | 정상 | 단일 화합물 (captan, trainset 홀드아웃 test 분자) | exit 0, 1 ok / 0 error | exit 0, 1 ok / 0 error | 0.0e+00 (601개) | 일치 |
| N2 | 정상 | 10건 일괄 예측 (CSV) | exit 0, 10 ok / 0 error | exit 0, 10 ok / 0 error | 0.0e+00 (6010개) | 일치 |
| N3 | 정상 | 나트륨 염·이온화 raw SMILES (.smi 입력) — 학습과 동일하게 그대로 예측, 경고 표시 | exit 0, 1 ok / 0 error, warn W-FEAT-001,W-STD-001,W-STD-002 | exit 0, 1 ok / 0 error, warn W-FEAT-001,W-STD-001,W-STD-002 | 0.0e+00 (601개) | 일치 |

## 3. 보조 시험 결과 (`/tests/cases/`)

| 사례 | 구분 | 입력 요약 | 기대 결과 | 실제 결과 | 확률 최대 오차 | 일치 |
|---|---|---|---|---|---|---|
| S1 | 오류 | 요청당 최대 건수 초과 101건 (serve) | HTTP 413, E-INPUT-003 | HTTP 413, E-INPUT-003 | — | 일치 |
| S2 | 오류 | 빈 요청 목록 (serve) | HTTP 422, E-INPUT-006 | HTTP 422, E-INPUT-006 | — | 일치 |
| S3 | 오류 | smiles 컬럼이 없는 CSV (batch) | exit 2, E-INPUT-005 | exit 2, E-INPUT-005 | — | 일치 |
| S4 | 오류 | 지원하지 않는 입력 형식 .xlsx (batch) | exit 2, E-INPUT-004 | exit 2, E-INPUT-004 | — | 일치 |
| S5 | 경계 | 체크포인트 재시작 — CHUNK_SIZE=3, MAX_CHUNKS_PER_RUN=2로 중단 후 재실행 (N2와 동일 결과) | exit [5, 0], 10 ok / 0 error | exit [5, 0], 10 ok / 0 error | 0.0e+00 (6010개) | 일치 |
| S6 | 정상 | STANDARDIZE=1 — 염 제거·전하 중화 후 예측 (N3과 같은 입력) | exit 0, 1 ok / 0 error, warn W-STD-001,W-STD-002,W-STD-003 | exit 0, 1 ok / 0 error, warn W-STD-001,W-STD-002,W-STD-003 | 0.0e+00 (601개) | 일치 |
| S7 | 경계 | 정상·오류 혼합 요청 — 200 응답에 행별 오류 포함 (serve) | HTTP 200, 2 ok / 1 error | HTTP 200, 2 ok / 1 error | 0.0e+00 (1202개) | 일치 |
| S8 | 정상 | 전하 분리 없이 표기한 니트로기 raw SMILES — RDKit이 [N+](=O)[O-]로 자동 정규화, 올바른 표기와 동일 예측 | exit 0, 2 ok / 0 error, warn W-STD-002 | exit 0, 2 ok / 0 error, warn W-STD-002 | 0.0e+00 (1202개) | 일치 |
| S9 | 경계 | RDKit 버전 의존 구조 — [AlH3] 알루미늄 착물(구버전 RDKit에서는 유효)은 E-INPUT-002, 나머지 행은 계속 | exit 0, 1 ok / 1 error, E-INPUT-002 | exit 0, 1 ok / 1 error, E-INPUT-002 | 0.0e+00 (601개) | 일치 |

## 4. 추가 검증 (재현성·정확성)

| 항목 | 방법 | 결과 |
|---|---|---|
| 반복 실행 결정성 (GPU) | seed0 test 506분자를 RTX 2080 Ti와 GTX 1080 Ti에서 각각 batch 실행해 비교 | 최대 절대오차 **0** (304,106개 확률값), 라벨 불일치 0 |
| 장치 간 결정성 (GPU ↔ CPU) | 같은 입력을 `DEVICE=cpu`로 실행해 비교 | 최대 절대오차 **0**, 모든 열 일치 |
| batch ↔ serve 일치 | B1(100건) serve 응답과 같은 분자의 batch 결과 비교 | 최대 절대오차 **0**, 601개 태스크 라벨 일치 |
| 평가 성능 재현 | 컨테이너 예측으로 seed0 test 지표를 다시 계산해 학습 환경(float32) 재채점값과 비교 | F1 0.153997 / 민감도 0.264900 / 특이도 0.754410 / 평가 태스크 534개 — 일치. AUROC 0.599252 vs 0.597232 — 분자별 확률 차이 최대 3×10⁻⁵이나 포화 확률(0·1)의 동점 처리 차이로 순위가 바뀜(`docs/model_card.md` 4.3) |
| 금속 착물 처리 | RDKit 2026에서 canonical SMILES가 바뀌는 5개 분자(코발라민 4, 유기납 1)를 입력 문자열에서 바로 그래프로 변환하는지 확인 | 학습 경로(`smiles_to_bigraph`)와 같은 그래프 사용 |
| 오프라인 실행 | 모든 시험을 `--network none`으로 실행 | 정상 동작 |
| 비루트 실행 | 이미지 `User` 설정, 출력 파일 소유자 | UID 10001 (`app`) |
| 가중치 무결성 | 시작 시 `models/SHA256SUMS` 1,203개 항목 검증 | 모두 일치 |
| 자원 사용량 (RTX 2080 Ti, 506분자) | `docker stats`, `nvidia-smi` 1초 간격 표본 | 최대 RAM 0.63 GiB, 최대 GPU 메모리 0.7 GB, 처리량 50.3 분자/초, 시작(체크섬+모델 601개 구성) 약 60초 |
| CPU 처리량 | 같은 506분자, `DEVICE=cpu`, 다른 작업 없는 상태 | 0.9 분자/초 (9분 59초) |

결정성 측정(위 첫 두 줄)은 최종 이미지와 `src/`·가중치가 같은 직전 빌드
(`sha256:e4867df07543…`)로 수행했다. 최종 이미지와의 차이는 `README.md`,
`tool.yaml`, `models/README.md` 문서 파일뿐이다.

## 5. 사례별 파일

각 사례 디렉터리에 입력 파일과 기대 결과 파일이 쌍으로 있다.

* batch 사례: `input.*` → `expected.csv` (`case.json`에 환경 변수·기대 종료 코드)
* serve 사례: `request.json` → `expected.json` (`case.json`에 기대 HTTP 상태)

재실행: `python3 tests/run_tests.py --image <이미지>` (GPU 없으면 `--cpu`).
