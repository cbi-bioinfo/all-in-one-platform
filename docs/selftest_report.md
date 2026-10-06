# 자체 시험 결과서 — FP-GNN Toxicity Predictor 1.0.0

## 1. 시험 환경

| 항목 | 값 |
|---|---|
| 이미지 | `pzkeung/bio-synergy-platform:fp-gnn-1.0.0` |
| 이미지 ID | `sha256:661206e5df7680cef84d75d0f19b5793ba44576b8bbbcbbdc2f429d4e89b635d` |
| 실행 장치 | GPU |
| 네트워크 | `--network none` (모든 사례) |
| 실행 시각 | 2026-10-06T09:16:12+09:00 |
| 시험 도구 | `tests/run_tests.py` |
| 허용 오차 | 확률값 절대오차 1e-06 이내, 문자열·판정값(라벨·상태·코드·메시지·경고·HTTP 상태·종료 코드)은 완전 일치 |

**결과: 18/18 일치**

## 2. 골든 데이터셋 시험 결과 (`/tests/golden/`)

| 사례 | 구분 | 입력 요약 | 기대 결과 | 실제 결과 | 확률 최대 오차 | 일치 |
|---|---|---|---|---|---|---|
| B1 | 경계 | 요청당 최대 건수 100건 (serve) | HTTP 200, 100 ok / 0 error | HTTP 200, 100 ok / 0 error | 0.0e+00 (63100개) | 일치 |
| B2 | 경계 | 입체 표기 [C@H] 포함 vs 제거 분자 — 키랄 태그가 원자 특징에 들어가 두 예측이 약간 다름 | exit 0, 2 ok / 0 error | exit 0, 2 ok / 0 error | 0.0e+00 (1262개) | 일치 |
| E1 | 오류 | 고리 미종결 SMILES (serve, 단일 요청) | HTTP 422, E-INPUT-002 | HTTP 422, E-INPUT-002 | — | 일치 |
| E2 | 오류 | 전하 표기가 빠진 4급 암모늄염 raw SMILES — 원자가 오류 행만 E-INPUT-002, 나머지 계속 | exit 0, 1 ok / 1 error, E-INPUT-002, warn W-FEAT-002,W-STD-001,W-STD-002 | exit 0, 1 ok / 1 error, E-INPUT-002, warn W-FEAT-002,W-STD-001,W-STD-002 | 0.0e+00 (631개) | 일치 |
| N1 | 정상 | 단일 화합물 (captan, trainset 홀드아웃 seed0 test 분자) | exit 0, 1 ok / 0 error | exit 0, 1 ok / 0 error | 0.0e+00 (631개) | 일치 |
| N2 | 정상 | 10건 일괄 예측 (CSV, seed0 test 분자) | exit 0, 10 ok / 0 error | exit 0, 10 ok / 0 error | 0.0e+00 (6310개) | 일치 |
| N3 | 정상 | 나트륨 염·이온화 raw SMILES (.smi 입력) — 염 포함 그대로 예측, W-STD·W-FEAT 경고 | exit 0, 1 ok / 0 error, warn W-FEAT-001,W-FEAT-002,W-STD-001,W-STD-002 | exit 0, 1 ok / 0 error, warn W-FEAT-001,W-FEAT-002,W-STD-001,W-STD-002 | 0.0e+00 (631개) | 일치 |

## 3. 보조 시험 결과 (`/tests/cases/`)

| 사례 | 구분 | 입력 요약 | 기대 결과 | 실제 결과 | 확률 최대 오차 | 일치 |
|---|---|---|---|---|---|---|
| S1 | 오류 | 요청당 최대 건수 초과 101건 (serve) | HTTP 413, E-INPUT-003 | HTTP 413, E-INPUT-003 | — | 일치 |
| S10 | 경계 | 백금 착물 배위결합(->) vs 단일결합 표기 — 둘 다 예측, Pt 혼성이 인코딩 범주 밖이라 W-FEAT-001 | exit 0, 2 ok / 0 error, warn W-FEAT-001 | exit 0, 2 ok / 0 error, warn W-FEAT-001 | 0.0e+00 (1262개) | 일치 |
| S11 | 경계 | 결합이 없는 무기염 KI (trainset 분자) — 고립 이온은 그래프 주의가 전체 원자로 퍼짐, W-FEAT-002 | exit 0, 1 ok / 0 error, warn W-FEAT-001,W-FEAT-002,W-STD-001,W-STD-002 | exit 0, 1 ok / 0 error, warn W-FEAT-001,W-FEAT-002,W-STD-001,W-STD-002 | 0.0e+00 (631개) | 일치 |
| S2 | 오류 | 빈 요청 목록 (serve) | HTTP 422, E-INPUT-006 | HTTP 422, E-INPUT-006 | — | 일치 |
| S3 | 오류 | smiles 컬럼이 없는 CSV (batch) | exit 2, E-INPUT-005 | exit 2, E-INPUT-005 | — | 일치 |
| S4 | 오류 | 지원하지 않는 입력 형식 .xlsx (batch) | exit 2, E-INPUT-004 | exit 2, E-INPUT-004 | — | 일치 |
| S5 | 경계 | 체크포인트 재시작 — CHUNK_SIZE=3, MAX_CHUNKS_PER_RUN=2로 중단 후 재실행 (N2와 동일 결과) | exit [5, 0], 10 ok / 0 error | exit [5, 0], 10 ok / 0 error | 0.0e+00 (6310개) | 일치 |
| S6 | 정상 | STANDARDIZE=1 — 염 제거·전하 중화 후 예측 (N3과 같은 입력) | exit 0, 1 ok / 0 error, warn W-STD-001,W-STD-002,W-STD-003 | exit 0, 1 ok / 0 error, warn W-STD-001,W-STD-002,W-STD-003 | 0.0e+00 (631개) | 일치 |
| S7 | 경계 | 정상·오류 혼합 요청 — 200 응답에 행별 오류 포함 (serve) | HTTP 200, 2 ok / 1 error | HTTP 200, 2 ok / 1 error | 0.0e+00 (1262개) | 일치 |
| S8 | 정상 | 전하 분리 없이 표기한 니트로기 raw SMILES — RDKit이 [N+](=O)[O-]로 자동 정규화, 올바른 표기와 동일 예측 | exit 0, 2 ok / 0 error, warn W-STD-002 | exit 0, 2 ok / 0 error, warn W-STD-002 | 0.0e+00 (1262개) | 일치 |
| S9 | 경계 | RDKit 버전 의존 구조 — [AlH3] 알루미늄 착물(RDKit 2026.3.6에서 원자가 초과)은 E-INPUT-002, 나머지 행은 계속 | exit 0, 1 ok / 1 error, E-INPUT-002 | exit 0, 1 ok / 1 error, E-INPUT-002 | 0.0e+00 (631개) | 일치 |

## 4. 추가 검증 (재현성·정확성)

측정 환경: GTX 1080 Ti(`--gpus device=1`), 같은 서버에서 다른 시험 작업이 함께 GPU를 사용하는 상태.

| 항목 | 방법 | 결과 |
|---|---|---|
| 학습 코드와의 계산 동등성 | 학습에 쓴 FP-GNN 코드와 본 패키지 엔진을 같은 입력에 적용 | 원자 특징 221,699개(trainset 전체) 완전 일치, 분자 지문 3,000개 완전 일치, PubChem 지문 10,966분자 완전 일치(PyBioMed 원본 대 학습 사본), seed0 test 확률 차이 최대 1.6×10⁻⁶(학습 코드 float32 대 본 엔진 float64) |
| 반복 실행 결정성 (GPU) | seed0 test 506분자를 같은 GPU에서 2회 batch 실행해 비교 | 최대 절대오차 **0** (319,286개 확률값), 모든 열 일치 |
| 장치 간 결정성 (GPU ↔ CPU) | 같은 입력을 `DEVICE=cpu`로 실행해 비교 | 최대 절대오차 **0**, 모든 열 일치 |
| batch ↔ serve 일치 | B1(100건) serve 응답과 같은 분자의 batch 결과 비교 | 최대 절대오차 **0**, 631개 태스크 라벨 일치 |
| 평가 성능 재현 | 컨테이너 예측으로 seed0 test 지표를 다시 계산해 학습 환경 재채점값과 비교 | AUROC 0.712695 / F1 0.272238 / 민감도 0.261550 / 특이도 0.874613, 평가 태스크 551개 — 소수점 6자리까지 일치 |
| 오프라인 실행 | 모든 시험을 `--network none`으로 실행 | 정상 동작 |
| 비루트 실행 | 이미지 `User` 설정, 출력 파일 소유자 | UID 10001 (`app`) |
| 가중치 무결성 | 시작 시 `models/SHA256SUMS` 검증 | 2개 파일 일치 |
| 자원 사용량 (trainset 10,974분자) | `docker stats` 1초 간격 표본 71개, 컨테이너 안 `torch.cuda.max_memory_reserved` | 최대 RAM 0.77 GiB, GPU 최대 할당 64 MiB, 처리량 66.4 분자/초(예측 단계), 전체 3분 3초(결과 파일 쓰기 포함), 오류 8건(RDKit이 거부하는 알루미늄 착물) |
| CPU 처리량 | seed0 test 506분자, `DEVICE=cpu` | 3.1 분자/초 (2분 45초) |
| 모델 로드 | 체크섬 검증 포함 | 약 1초 |

결정성·자원 측정은 최종 이미지와 `src/`·`models/*.pt`·`requirements.lock`이 같은 직전 빌드로 수행했다. 최종 이미지와의 차이는 이미지에 복사되는 문서 파일(`README.md`, `tool.yaml`, `models/README.md`)뿐이다.

## 5. 사례별 파일

각 사례 디렉터리에 입력 파일과 기대 결과 파일이 쌍으로 있다.

* batch 사례: `input.*` → `expected.csv` (`case.json`에 환경 변수·기대 종료 코드)
* serve 사례: `request.json` → `expected.json` (`case.json`에 기대 HTTP 상태)

재실행: `python3 tests/run_tests.py --image <이미지>` (GPU 없으면 `--cpu`).
